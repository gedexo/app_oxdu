from decimal import Decimal
from django.db import transaction as db_transaction
from transactions.models import Transaction, TransactionEntry
from accounting.utils import get_system_account
from admission.models import FeeReceipt


def post_fee_due(structure):
    """
    Posts accounting ONLY when a fee becomes due.
    Safe, idempotent, auditable.
    """

    if not structure.student or not structure.student.branch:
        return None

    if structure.amount <= 0:
        return None

    # Prevent duplicate posting
    if structure.transaction:
        return structure.transaction

    student = structure.student
    branch = student.branch

    income_account = get_system_account(branch, 'TUITION_FEE')

    with db_transaction.atomic():
        trans = Transaction.objects.create(
            transaction_type='course_fee',
            voucher_number=f"FEE-DUE-{structure.pk}",
            date=structure.due_date,
            branch=branch,
            status='posted',
            is_double_entry=True,
            invoice_amount=structure.amount,
            total_amount=structure.amount,
            received_amount=Decimal('0.00'),
            balance_amount=structure.amount,
            narration=f"Tuition Fee Due - {student.fullname()}"
        )

        # Student Dr
        TransactionEntry.objects.create(
            transaction=trans,
            account=student.account,
            debit_amount=structure.amount,
            credit_amount=0,
            description="Tuition Fee Due"
        )

        # Income Cr
        TransactionEntry.objects.create(
            transaction=trans,
            account=income_account,
            debit_amount=0,
            credit_amount=structure.amount,
            description="Tuition Fee Income"
        )

        structure.transaction = trans
        structure.save(update_fields=['transaction'])

        return trans


from django.db.models import Sum


def post_fee_receipt(receipt):
    if not receipt.student or not receipt.student.account:
        return None

    total_amount = receipt.payment_methods.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    if total_amount <= 0:
        return None

    branch = receipt.student.branch

    with db_transaction.atomic():
        trans = receipt.transaction
        if not trans:
            trans = Transaction.objects.create(
                transaction_type='receipt',
                voucher_number=receipt.receipt_no,
                date=receipt.date,
                branch=branch,
                status='posted',
                is_double_entry=True
            )

        trans.invoice_amount = total_amount
        trans.total_amount = total_amount
        trans.received_amount = total_amount
        trans.balance_amount = Decimal('0.00')
        trans.narration = f"Fee Received - {receipt.student.fullname()}"
        trans.save()

        # 🔑 SAFE update (no signal fired)
        FeeReceipt.objects.filter(pk=receipt.pk).update(transaction=trans)

        # Reset entries
        trans.entries.all().delete()

        # Student Cr
        TransactionEntry.objects.create(
            transaction=trans,
            account=receipt.student.account,
            debit_amount=0,
            credit_amount=total_amount,
            description="Fee Payment Received"
        )

        cash = get_system_account(branch, 'CASH_ON_HAND')
        bank = get_system_account(branch, 'MAIN_BANK_ACCOUNT')

        for pm in receipt.payment_methods.all():
            target = cash if pm.payment_type == 'CASH' else bank
            TransactionEntry.objects.create(
                transaction=trans,
                account=target,
                debit_amount=pm.amount,
                credit_amount=0,
                description=pm.get_payment_type_display()
            )

        return trans