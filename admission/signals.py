# admission/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction as db_transaction
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal

from admission.models import FeeReceipt, PaymentMethod, FeeStructure, Admission
from accounting.models import Account, GroupMaster
from transactions.models import Transaction, TransactionEntry
from admission.models import FeeReceipt
from accounting.utils import get_system_account


def get_or_create_current_assets(branch):
    return GroupMaster.objects.get_or_create(
        branch=branch,
        code="CURRENT_ASSETS",
        defaults={
            "name": "Current Assets",
            "nature_of_group": "Assets",
            "main_group": "balance_sheet",
            "is_locked": True,
            "locking_group": "CURRENT_ASSETS",
        },
    )[0]

def get_or_create_sundry_debtors(branch):
    parent = get_or_create_current_assets(branch)

    return GroupMaster.objects.get_or_create(
        branch=branch,
        code="SUNDRY_DEBTORS",
        defaults={
            "name": "Sundry Debtors",
            "parent": parent,
            "nature_of_group": "Assets",
            "main_group": "balance_sheet",
            "is_locked": True,
            "locking_group": "SUNDRY_DEBTORS",
        },
    )[0]


def get_or_create_student_group(branch):
    parent = get_or_create_sundry_debtors(branch)

    return GroupMaster.objects.get_or_create(
        branch=branch,
        code="STUDENTS",
        defaults={
            "name": "Students",
            "parent": parent,
            "nature_of_group": "Assets",
            "main_group": "balance_sheet",
            "is_locked": True,
            "locking_group": "STUDENTS",
            "description": "System generated Students group",
        },
    )[0]


def generate_student_account_code(branch, student):
    """
    Generates branch-safe student account code
    """
    base = student.admission_number or str(student.pk)
    return f"{branch.id:03d}-STD-{base}"


@receiver(post_save, sender=Admission)
def create_student_account(sender, instance, created, **kwargs):
    """
    Auto-create student ledger on admission creation
    """
    if not created:
        return

    if instance.account or not instance.branch:
        return

    with transaction.atomic():
        group = get_or_create_student_group(instance.branch)

        account = Account.objects.create(
            branch=instance.branch,
            ledger_type="STUDENT",
            code=generate_student_account_code(instance.branch, instance),
            name=instance.fullname(),
            alias_name=instance.admission_number,
            under=group,
        )

        instance.account = account
        instance.save(update_fields=["account"])


# =========================================================
@receiver(post_save, sender=FeeReceipt)
def receipt_saved(sender, instance, **kwargs):
    from admission.services.fee_accounting import post_fee_receipt
    if instance.payment_methods.exists():
        post_fee_receipt(instance)

@receiver(post_delete, sender=PaymentMethod)
def receipt_payment_deleted(sender, instance, **kwargs):
    
    from admission.services.fee_accounting import post_fee_receipt
    post_fee_receipt(instance.fee_receipt)

@receiver(post_save, sender=PaymentMethod)
def payment_method_changed(sender, instance, **kwargs):
    from admission.services.fee_accounting import post_fee_receipt
    post_fee_receipt(instance.fee_receipt)