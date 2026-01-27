from django.core.management.base import BaseCommand
from employees.models import Employee, EmployeeLeaveBalance
from datetime import date

class Command(BaseCommand):
    help = 'Updates leave balances for ALL employees for the new month'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Monthly Leave Accrual...")
        
        employees = Employee.objects.all()
        count = 0

        for employee in employees:
            # Get or Create ensures we don't crash on missing records
            balance, created = EmployeeLeaveBalance.objects.get_or_create(
                employee=employee,
                defaults={'paid_leave_balance': 1.0, 'wfh_balance': 1.0}
            )
            
            # This function (defined in your models.py) checks the date
            # and adds the new leaves if a month has passed.
            balance.accrue_monthly()
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully updated balances for {count} employees."))