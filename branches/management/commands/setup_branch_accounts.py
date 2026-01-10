from django.core.management.base import BaseCommand
from django.db import transaction

from branches.models import Branch
from branches.signals import (
    validate_branch_accounts,
    create_missing_accounts_for_branch,
)


class Command(BaseCommand):
    help = "Create missing default accounting groups and accounts for branches"

    def handle(self, *args, **options):
        branches = Branch.objects.all()
        self.stdout.write(f"🏢 Found {branches.count()} branches")

        for branch in branches:
            self.stdout.write(f"\nProcessing: {branch.name} (ID {branch.id})")

            try:
                with transaction.atomic():
                    if validate_branch_accounts(branch):
                        self.stdout.write(
                            self.style.SUCCESS("✔ Already configured")
                        )
                        continue

                    created = create_missing_accounts_for_branch(branch)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✔ Created {len(created)} missing accounts"
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✖ Failed: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS("\n🎉 Branch accounting setup complete")
        )
