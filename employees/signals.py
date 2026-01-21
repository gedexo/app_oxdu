from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Employee
from accounting.models import Account, GroupMaster
from accounting.constants import ACCOUNT_CODE_MAPPING
from .models import Employee, Payroll, PayrollPayment, AdvancePayrollPayment


@receiver(post_save, sender=Employee)
def create_employee_account_signal(sender, instance, created, **kwargs):
    # Only run if it's a new employee and they don't have an account linked
    if created and not instance.account:
        transaction.on_commit(lambda: create_account_for_employee(instance))

def create_account_for_employee(employee):
    if employee.account:
        return

    group_code = 'ADVANCE_TO_EMPLOYEES'
    
    try:
        # Find the group master for this specific branch
        group = GroupMaster.objects.get(code=group_code, branch=employee.branch)

        # Generate unique code
        base_code = ACCOUNT_CODE_MAPPING.get(group_code, "12002")
        unique_code = f"{base_code}-{employee.pk}"

        # Create the Account matching your Account model fields
        new_account = Account.objects.create(
            branch=employee.branch,
            ledger_type='EMPLOYEE',
            code=unique_code,
            name=f"Employee - {employee.fullname()}",
            under=group,  # Changed from 'group' to 'under'
            is_locked=True,
            locking_account='ADVANCE_TO_STAFF' # From your LOCKED_ACCOUNT_CHOICES
        )

        # Link and save
        employee.account = new_account
        employee.save(update_fields=['account'])
        
    except GroupMaster.DoesNotExist:
        print(f"Error: GroupMaster '{group_code}' not found for branch {employee.branch}")
    except Exception as e:
        print(f"Error creating account for employee {employee.pk}: {str(e)}")

    
@receiver(post_save, sender=Payroll)
def update_payroll_accounting(sender, instance, created, **kwargs):
    # We only create accounting entries if the status is "Approved" or finalized
    if instance.status == "Approved":
        instance.create_accounting_entry()

@receiver(post_save, sender=PayrollPayment)
def update_payment_accounting(sender, instance, created, **kwargs):
    instance.create_accounting_entry()

@receiver(post_save, sender=AdvancePayrollPayment)
def update_advance_accounting(sender, instance, created, **kwargs):
    # Logic for Advance is similar to PayrollPayment:
    # Debit: Employee Account (Advance Asset)
    # Credit: Bank/Cash
    instance.create_accounting_entry()