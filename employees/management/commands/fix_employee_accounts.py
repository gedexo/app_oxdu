from django.core.management.base import BaseCommand
from django.db import transaction
from employees.models import Employee
from accounting.models import Account, GroupMaster
from accounting.constants import ACCOUNT_CODE_MAPPING

class Command(BaseCommand):
    help = 'Creates accounting accounts for existing employees who do not have one'

    def handle(self, *args, **options):
        group_code = 'ADVANCE_TO_EMPLOYEES'
        
        # 1. Identify employees without accounts
        employees_without_accounts = Employee.objects.filter(account__isnull=True)
        total = employees_without_accounts.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("All employees already have accounts."))
            return

        self.stdout.write(f"Found {total} employees without accounts. Starting...")

        success_count = 0
        
        with transaction.atomic():
            for emp in employees_without_accounts:
                try:
                    # Get the group for the specific branch of this employee
                    group = GroupMaster.objects.get(code=group_code, branch=emp.branch)
                    
                    base_code = ACCOUNT_CODE_MAPPING.get(group_code, "12002")
                    unique_code = f"{base_code}-{emp.pk}"
                    
                    if Account.objects.filter(code=unique_code, branch=emp.branch).exists():
                        unique_code = f"{base_code}-{emp.pk}-FIX"

                    # Create account using your exact model structure
                    acc = Account.objects.create(
                        branch=emp.branch,
                        ledger_type='EMPLOYEE',
                        code=unique_code,
                        name=f"Employee - {emp.fullname()}",
                        under=group, # Model uses 'under'
                        is_locked=True,
                        locking_account='ADVANCE_TO_STAFF'
                    )
                    
                    emp.account = acc
                    emp.save(update_fields=['account'])
                    
                    success_count += 1
                    self.stdout.write(f"Linked: {emp.fullname()} to {unique_code}")
                
                except GroupMaster.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"Skipped {emp.fullname()}: Group '{group_code}' not found in branch {emp.branch}"
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error for {emp.fullname()}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Finished. Successfully linked {success_count} accounts."))