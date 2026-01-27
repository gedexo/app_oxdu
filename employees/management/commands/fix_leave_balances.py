from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from employees.models import Employee, EmployeeLeaveBalance

class Command(BaseCommand):
    help = 'Fixes employee leave balances: sets 0.0 balances to 1.0 for startup.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting Leave Balance Fix..."))
        
        employees = Employee.objects.all()
        count = 0

        for employee in employees:
            # Get or Create the balance record
            # We use defaults here to ensure NEW records start at 1.0
            balance, created = EmployeeLeaveBalance.objects.get_or_create(
                employee=employee,
                defaults={
                    'paid_leave_balance': 1.0, 
                    'wfh_balance': 1.0,
                    'last_accrual_month': date.today().replace(day=1)
                }
            )

            updated = False
            
            # If record existed but has 0.0 balance (and likely hasn't been used yet), fix it.
            # We check if it is less than 1.0
            if balance.paid_leave_balance < 1.0:
                balance.paid_leave_balance = 1.0
                updated = True
            
            if balance.wfh_balance < 1.0:
                balance.wfh_balance = 1.0
                updated = True

            if updated or created:
                # Reset the accrual date to avoid double counting for this specific month
                balance.last_accrual_month = date.today().replace(day=1)
                balance.save()
                count += 1
                self.stdout.write(f"Fixed balance for: {employee.fullname}")

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {employees.count()} employees."))
        self.stdout.write(self.style.SUCCESS(f"Updated/Created balances for {count} employees."))