from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.utils import timezone

from employees.models import Employee, Payroll, PayrollPayment
from accounting.models import Account, GroupMaster
from transactions.models import Transaction, TransactionEntry
from accounting.constants import ACCOUNT_CODE_MAPPING


class Command(BaseCommand):
    help = 'Recursion-safe payroll sync with auto ledger creation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n--- Starting Payroll → Accounting Sync ---"
        ))

        self.fix_employee_ledgers()
        self.sync_payments()
        self.sync_provisions()

        self.stdout.write(self.style.SUCCESS(
            "--- Payroll Accounting Sync Finished ---\n"
        ))

    # --------------------------------------------------
    # STEP 1: ENSURE EMPLOYEE LEDGERS EXIST
    # --------------------------------------------------
    def fix_employee_ledgers(self):
        self.stdout.write("Step 1: Fixing Employee Ledgers...")

        group_code = 'ADVANCE_TO_EMPLOYEES'

        for emp in Employee.objects.filter(account__isnull=True):
            try:
                group = GroupMaster.objects.get(
                    code=group_code,
                    branch=emp.branch
                )

                unique_code = f"{ACCOUNT_CODE_MAPPING.get(group_code, '12002')}-{emp.pk}"

                acc, _ = Account.objects.get_or_create(
                    code=unique_code,
                    branch=emp.branch,
                    defaults={
                        'ledger_type': 'EMPLOYEE',
                        'name': f"{emp.fullname()}",
                        'under': group
                    }
                )

                Employee.objects.filter(pk=emp.pk).update(account=acc)

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  - Employee {emp.pk} skipped: {e}")
                )

    # --------------------------------------------------
    # STEP 2: PAYROLL PAYMENTS → TRANSACTIONS
    # --------------------------------------------------
    def sync_payments(self):
        self.stdout.write("Step 2: Syncing Payroll Payments...")

        payments = PayrollPayment.objects.filter(transaction__isnull=True)

        for pay in payments:
            try:
                emp = Employee.objects.filter(
                    pk=pay.employee_id
                ).values('account_id', 'branch_id').first()

                if not emp or not emp['account_id']:
                    self.stdout.write(
                        self.style.WARNING(f"  - Payment {pay.pk} skipped: No employee ledger")
                    )
                    continue

                branch_id = emp['branch_id']
                emp_acc_id = emp['account_id']

                method = str(pay.payment_method).lower()
                cash_or_bank = '11001' if 'bank' in method or 'online' in method else '10001'

                bank_acc = Account.objects.filter(
                    code=cash_or_bank,
                    branch_id=branch_id
                ).first()

                if not bank_acc:
                    self.stdout.write(
                        self.style.ERROR(f"  - Payment {pay.pk} FAILED: Missing {cash_or_bank}")
                    )
                    continue

                with db_transaction.atomic():
                    trans = Transaction.objects.create(
                        branch_id=branch_id,
                        transaction_type='payroll',
                        status='posted',
                        date=timezone.now(),
                        voucher_number=f"PMT-{pay.pk}",
                        invoice_amount=pay.amount_paid,
                        total_amount=pay.amount_paid
                    )

                    TransactionEntry.objects.create(
                        transaction=trans,
                        account_id=emp_acc_id,
                        debit_amount=pay.amount_paid,
                        credit_amount=0
                    )

                    TransactionEntry.objects.create(
                        transaction=trans,
                        account_id=bank_acc.id,
                        debit_amount=0,
                        credit_amount=pay.amount_paid
                    )

                    PayrollPayment.objects.filter(pk=pay.pk).update(
                        transaction=trans,
                        paid_from=bank_acc.id
                    )

                self.stdout.write(
                    self.style.SUCCESS(f"  ✔ Payment Synced {pay.pk}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✖ Payment {pay.pk} FAILED: {e}")
                )

    # --------------------------------------------------
    # STEP 3: PAYROLL PROVISIONS → TRANSACTIONS (FIXED)
    # --------------------------------------------------
    def sync_provisions(self):
        self.stdout.write("Step 3: Syncing Payroll Provisions...")

        payrolls = Payroll.objects.filter(
            transaction__isnull=True,
            net_salary__gt=0
        )

        for p in payrolls:
            try:
                emp = Employee.objects.filter(
                    pk=p.employee_id
                ).values('account_id', 'branch_id').first()

                if not emp or not emp['account_id']:
                    self.stdout.write(
                        self.style.WARNING(f"  - Payroll {p.pk} skipped: No employee ledger")
                    )
                    continue

                # Prevent duplicates
                if Transaction.objects.filter(
                    voucher_number=f"PROV-{p.pk}"
                ).exists():
                    continue

                branch_id = emp['branch_id']
                emp_acc_id = emp['account_id']

                is_teacher = bool(
                    p.employee.designation and
                    "teacher" in p.employee.designation.name.lower()
                )

                # ✅ Correct group mapping
                parent_group_code = 'STAFF_EXPENSES'
                salary_group_code = (
                    'TEACHING_STAFF_SALARY'
                    if is_teacher else
                    'NON_TEACHING_STAFF_SALARY'
                )

                salary_name = (
                    'Teaching Staff Salary'
                    if is_teacher else
                    'Non-Teaching Staff Salary'
                )

                # --------------------------------------------------
                # 1️⃣ Ensure STAFF_EXPENSES group exists
                # --------------------------------------------------
                staff_group, _ = GroupMaster.objects.get_or_create(
                    code=parent_group_code,
                    branch_id=branch_id,
                    defaults={
                        'name': 'Staff Expenses',
                        'main_group': 'EXPENSES',
                        'nature_of_group': 'DEBIT'
                    }
                )

                # --------------------------------------------------
                # 2️⃣ Ensure Salary subgroup exists
                # --------------------------------------------------
                salary_group, _ = GroupMaster.objects.get_or_create(
                    code=salary_group_code,
                    branch_id=branch_id,
                    defaults={
                        'name': salary_name,
                        'parent': staff_group,
                        'main_group': 'EXPENSES',
                        'nature_of_group': 'DEBIT'
                    }
                )

                # --------------------------------------------------
                # 3️⃣ Ensure Expense Ledger exists
                # --------------------------------------------------
                ledger_code = '50001' if is_teacher else '50002'

                expense_account, _ = Account.objects.get_or_create(
                    code=ledger_code,
                    branch_id=branch_id,
                    defaults={
                        'name': salary_name,
                        'ledger_type': 'GENERAL',
                        'under': salary_group
                    }
                )

                # --------------------------------------------------
                # 4️⃣ Create Transaction
                # --------------------------------------------------
                with db_transaction.atomic():
                    trans = Transaction.objects.create(
                        branch_id=branch_id,
                        transaction_type='payroll',
                        status='posted',
                        date=timezone.now(),
                        voucher_number=f"PROV-{p.pk}",
                        narration=f"Salary provision - {p.employee.fullname()}",
                        invoice_amount=p.net_salary,
                        total_amount=p.net_salary
                    )

                    TransactionEntry.objects.create(
                        transaction=trans,
                        account=expense_account,
                        debit_amount=p.net_salary,
                        credit_amount=0,
                        description="Salary Expense Provision"
                    )

                    TransactionEntry.objects.create(
                        transaction=trans,
                        account_id=emp_acc_id,
                        debit_amount=0,
                        credit_amount=p.net_salary,
                        description="Salary Payable"
                    )

                    Payroll.objects.filter(pk=p.pk).update(transaction=trans)

                self.stdout.write(
                    self.style.SUCCESS(f"  ✔ Payroll Provision Synced {p.pk}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✖ Payroll {p.pk} FAILED: {e}")
                )
