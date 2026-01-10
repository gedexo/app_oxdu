from django.core.management.base import BaseCommand
from django.db import transaction

from admission.models import Admission
from accounting.models import Account
from admission.signals import (
    get_or_create_student_group,
    generate_student_account_code,
)


class Command(BaseCommand):
    help = "Create missing accounting accounts for students"

    def handle(self, *args, **options):
        students = Admission.objects.filter(account__isnull=True)
        self.stdout.write(f"👨‍🎓 Found {students.count()} students without accounts")

        for student in students:
            if not student.branch:
                continue

            # Safety check
            if Account.objects.filter(
                branch=student.branch,
                alias_name=student.admission_number,
                ledger_type="STUDENT",
            ).exists():
                continue

            with transaction.atomic():
                group = get_or_create_student_group(student.branch)

                account = Account.objects.create(
                    branch=student.branch,
                    ledger_type="STUDENT",
                    code=generate_student_account_code(student.branch, student),
                    name=student.fullname(),
                    alias_name=student.admission_number,
                    under=group,
                )

                student.account = account
                student.save(update_fields=["account"])

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✔ Created account for {student.fullname()}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS("🎉 Student account backfill completed")
        )
