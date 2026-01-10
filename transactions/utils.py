from django.db.models import Max


def generate_next_voucher_number(
    model,
    transaction_type,
    branch=None,
    lookup_field="voucher_number"
):
    """
    Generate next voucher number based on transaction_type and branch.
    Company is NOT used.
    """

    # Default prefixes
    PREFIXES = {
        'sale_invoice': 'SI',
        'sale_order': 'SO',
        'credit_note': 'CN',
        'purchase_invoice': 'PI',
        'purchase_order': 'PO',
        'debit_note': 'DN',
        'receipt': 'RCP',
        'payment': 'PAY',
        'journal_voucher': 'JV',
        'income': 'INC',
        'expense': 'EXP',
        'contra': 'CTR',
        'opening_balance': 'OB',
        'stock_adjustment': 'STK',
    }

    prefix = PREFIXES.get(transaction_type, 'INV')
    start_count = 1

    # Build filters
    filters = {
        "transaction_type": transaction_type,
        f"{lookup_field}__startswith": prefix,
    }

    if branch:
        filters["branch"] = branch

    # Use all_objects if soft delete exists
    manager = getattr(model, "all_objects", model.objects)

    # Get last voucher
    last_voucher = manager.filter(**filters).aggregate(
        max_voucher=Max(lookup_field)
    )["max_voucher"]

    # Calculate next number
    next_number = start_count
    if last_voucher:
        try:
            numeric_part = last_voucher.replace(prefix, "").lstrip("0")
            next_number = int(numeric_part) + 1 if numeric_part else start_count
        except ValueError:
            next_number = start_count

    return f"{prefix}{next_number:04d}"
