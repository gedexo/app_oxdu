from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Employee
from accounting.models import Account, GroupMaster
from accounting.constants import ACCOUNT_CODE_MAPPING
from .models import Employee, Payroll, PayrollPayment, AdvancePayrollPayment, EmployeeLeaveBalance


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

from django.db.models.signals import post_save
from django.dispatch import receiver
from employees.models import EmployeeLeaveRequest

@receiver(post_save, sender=EmployeeLeaveRequest)
def update_employee_balance(sender, instance, created, **kwargs):
    """
    Deduct leave only ONCE when status becomes approved
    """

    if instance.status != 'approved':
        return

    if instance.is_balance_deducted:
        return

    balance, _ = EmployeeLeaveBalance.objects.get_or_create(employee=instance.employee)

    days = instance.total_days or 0

    if instance.leave_type == 'wfh':
        balance.wfh_balance = max(balance.wfh_balance - days, 0)
    else: 
        balance.paid_leave_balance = max(balance.paid_leave_balance - days, 0)

    balance.save()

    instance.is_balance_deducted = True
    instance.save(update_fields=["is_balance_deducted"])


@receiver(post_save, sender=EmployeeLeaveRequest)
def manage_leave_balance(sender, instance, created, **kwargs):
    """
    Deducts balance when status changes to 'approved'.
    Refunds balance if status changes from 'approved' to 'rejected/pending'.
    """
    if not instance.pk:
        return

    # Only process if this is an existing record being updated
    # We need to fetch the employee balance
    try:
        balance = EmployeeLeaveBalance.objects.get(employee=instance.employee)
    except EmployeeLeaveBalance.DoesNotExist:
        # Create balance if it doesn't exist (safety net)
        balance = EmployeeLeaveBalance.objects.create(employee=instance.employee)
        balance.accrue_monthly() # Initialize with this month's stock

    # Check logic only if status is Approved and we haven't deducted yet
    if instance.status == 'approved' and not instance.is_balance_deducted:
        days_to_deduct = instance.total_days

        if instance.leave_type == 'wfh':
            if balance.wfh_balance >= days_to_deduct:
                balance.wfh_balance -= days_to_deduct
                instance.is_balance_deducted = True
                instance.save(update_fields=['is_balance_deducted'])
                balance.save()
            else:
                # Edge case: Admin approved but balance changed in background
                # In production, you might want to log this error or force reject
                pass 
        
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            if balance.paid_leave_balance >= days_to_deduct:
                balance.paid_leave_balance -= days_to_deduct
                instance.is_balance_deducted = True
                instance.save(update_fields=['is_balance_deducted'])
                balance.save()

    # Handle Reversal: If it WAS approved/deducted, but now is Rejected/Pending
    elif instance.status in ['rejected', 'pending'] and instance.is_balance_deducted:
        days_to_refund = instance.total_days
        
        if instance.leave_type == 'wfh':
            # Refund but do not exceed max limit + refund (optional logic, usually we just refund)
            balance.wfh_balance = min(balance.wfh_balance + days_to_refund, balance.MAX_WFH_LIMIT)
        
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            balance.paid_leave_balance = min(balance.paid_leave_balance + days_to_refund, balance.MAX_PAID_LIMIT)
        
        instance.is_balance_deducted = False
        instance.save(update_fields=['is_balance_deducted'])
        balance.save()

    
@receiver(post_save, sender=EmployeeLeaveRequest)
def leave_balance_handler(sender, instance, **kwargs):
    """
    Consolidated Signal:
    1. Deducts balance when Approved.
    2. Refunds balance if changed from Approved to Rejected/Pending.
    """
    if not instance.pk:
        return

    # Use get_or_create to ensure no "Does Not Exist" error
    balance, created = EmployeeLeaveBalance.objects.get_or_create(
        employee=instance.employee,
        defaults={'paid_leave_balance': 1.0, 'wfh_balance': 1.0}
    )
    
    # If we just created the balance in this signal, we don't need to deduct/refund yet
    # unless specific logic demands it, but usually, we just proceed.

    # CASE 1: Leave is APPROVED -> Deduct
    if instance.status == 'approved' and not instance.is_balance_deducted:
        days = instance.total_days
        if instance.leave_type == 'wfh':
            # Logic: If balance goes below 0, let it (or cap at 0). 
            # Ideally, form validation prevents this, but this is a safety net.
            balance.wfh_balance = max(0.0, balance.wfh_balance - days)
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            balance.paid_leave_balance = max(0.0, balance.paid_leave_balance - days)
        
        balance.save()
        # Mark as deducted
        instance.is_balance_deducted = True
        instance.save(update_fields=['is_balance_deducted'])

    # CASE 2: Leave was APPROVED, now REJECTED/PENDING -> Refund
    elif instance.status in ['rejected', 'pending'] and instance.is_balance_deducted:
        days = instance.total_days
        if instance.leave_type == 'wfh':
            balance.wfh_balance = min(balance.wfh_balance + days, balance.MAX_WFH_LIMIT)
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            balance.paid_leave_balance = min(balance.paid_leave_balance + days, balance.MAX_PAID_LIMIT)
            
        balance.save()
        instance.is_balance_deducted = False
        instance.save(update_fields=['is_balance_deducted'])

    
@receiver(post_save, sender=EmployeeLeaveRequest)
def leave_balance_controller(sender, instance, created, **kwargs):
    """
    Centralized logic to Deduct or Refund leave balances.
    """
    # 1. Skip if this is a new record (leave starts as 'pending', no deduction yet)
    #    Unless you auto-approve, which is rare.
    if created and instance.status != 'approved':
        return

    # 2. Get the Employee's Balance Board
    #    We use defaults to ensure we don't crash if it's missing (starts at 1.0)
    balance, _ = EmployeeLeaveBalance.objects.get_or_create(
        employee=instance.employee,
        defaults={'paid_leave_balance': 1.0, 'wfh_balance': 1.0}
    )

    # ---------------------------------------------------------
    # SCENARIO A: DEDUCT BALANCE (Status changed to Approved)
    # ---------------------------------------------------------
    if instance.status == 'approved' and not instance.is_balance_deducted:
        days_to_deduct = instance.total_days

        if instance.leave_type == 'wfh':
            # Deduct WFH
            new_balance = balance.wfh_balance - days_to_deduct
            balance.wfh_balance = max(0.0, new_balance) # Prevent negative
        
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            # Deduct Paid Leave
            new_balance = balance.paid_leave_balance - days_to_deduct
            balance.paid_leave_balance = max(0.0, new_balance) # Prevent negative

        # Save the Balance
        balance.save()

        # Mark request as deducted so we don't do it again
        instance.is_balance_deducted = True
        # Use update_fields to avoid triggering this signal again recursively
        instance.save(update_fields=['is_balance_deducted'])


    # ---------------------------------------------------------
    # SCENARIO B: REFUND BALANCE (Approved -> Rejected/Pending)
    # ---------------------------------------------------------
    elif instance.status in ['rejected', 'pending'] and instance.is_balance_deducted:
        days_to_refund = instance.total_days

        if instance.leave_type == 'wfh':
            # Add back WFH (Check against Max Limit)
            balance.wfh_balance = min(
                balance.wfh_balance + days_to_refund, 
                balance.MAX_WFH_LIMIT
            )
        
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            # Add back Paid Leave (Check against Max Limit)
            balance.paid_leave_balance = min(
                balance.paid_leave_balance + days_to_refund, 
                balance.MAX_PAID_LIMIT
            )

        # Save the Balance
        balance.save()

        # Unmark the flag
        instance.is_balance_deducted = False
        instance.save(update_fields=['is_balance_deducted'])


@receiver(post_save, sender=EmployeeLeaveRequest)
def manage_leave_balance_signal(sender, instance, created, **kwargs):
    """
    Single, Clean Signal to Deduct or Refund leaves.
    """
    # 1. Initialization: Get or Create Balance (Safe for new employees)
    balance, _ = EmployeeLeaveBalance.objects.get_or_create(
        employee=instance.employee,
        defaults={'paid_leave_balance': 1.0, 'wfh_balance': 1.0}
    )

    # 2. Scenario A: Deduct Balance (Status changed to Approved)
    if instance.status == 'approved' and not instance.is_balance_deducted:
        days_to_deduct = instance.total_days

        if instance.leave_type == 'wfh':
            # Deduct WFH
            balance.wfh_balance = max(0.0, balance.wfh_balance - days_to_deduct)
        
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            # Deduct Paid Leave
            balance.paid_leave_balance = max(0.0, balance.paid_leave_balance - days_to_deduct)

        balance.save()
        
        # Mark as deducted
        instance.is_balance_deducted = True
        instance.save(update_fields=['is_balance_deducted'])


    # 3. Scenario B: Refund Balance (Approved -> Rejected/Pending)
    elif instance.status in ['rejected', 'pending'] and instance.is_balance_deducted:
        days_to_refund = instance.total_days
        
        if instance.leave_type == 'wfh':
            # Add back balance. 
            balance.wfh_balance += days_to_refund
        
        elif instance.leave_type in ['sick', 'casual', 'emergency']:
            balance.paid_leave_balance += days_to_refund
        
        balance.save()

        instance.is_balance_deducted = False
        instance.save(update_fields=['is_balance_deducted'])