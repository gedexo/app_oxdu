from decimal import Decimal
from admission.models import FeeStructure, FeeReceipt

def calculate_student_fee_structure(student_id, exclude_receipt_id=None):
    """
    Calculate the fee structure state for a student, optionally excluding a specific receipt.
    This is useful for update views where we want to see the state *before* the current receipt was applied.
    """
    # 1. Fetch all fee structures
    fee_structures = list(FeeStructure.objects.filter(student_id=student_id).order_by('installment_no'))
    
    # 2. Reset paid amounts in memory
    for fs in fee_structures:
        fs.paid_amount = Decimal('0.00')
        fs.is_paid = False

    # 3. Fetch all receipts, excluding the one being updated if specified
    receipts_qs = FeeReceipt.objects.filter(student_id=student_id, is_active=True).order_by('date', 'id')
    
    if exclude_receipt_id:
        receipts_qs = receipts_qs.exclude(id=exclude_receipt_id)

    # 4. Replay allocation logic
    for receipt in receipts_qs:
        remaining = receipt.get_amount()
        
        # Get unpaid fees (from our in-memory list)
        # We need to filter the in-memory list, not query DB again
        unpaid_fees = [fs for fs in fee_structures if not fs.is_paid]
        
        # Sort by due_date (handling None values if any)
        # Assuming due_date is always present for installments, but let's be safe
        unpaid_fees.sort(key=lambda x: x.due_date if x.due_date else x.created)

        for fee in unpaid_fees:
            if remaining <= 0:
                break

            outstanding = fee.amount - fee.paid_amount
            pay = min(outstanding, remaining)

            fee.paid_amount += pay
            remaining -= pay

            if fee.paid_amount >= fee.amount:
                fee.is_paid = True

    return fee_structures
