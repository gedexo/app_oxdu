from django.core.management.base import BaseCommand
from admission.models import FeeStructure, FeeReceipt
from admission.services.fee_accounting import post_fee_due, post_fee_receipt


class Command(BaseCommand):
    help = "Sync Fee Due and Fee Receipts to Accounting"

    def handle(self, *args, **kwargs):
        self.stdout.write("Posting Fee Dues...")

        for fs in FeeStructure.objects.filter(
            is_active=True,
            transaction__isnull=True
        ):
            post_fee_due(fs)

        self.stdout.write("Posting Fee Receipts...")

        for receipt in FeeReceipt.objects.all():
            post_fee_receipt(receipt)

        self.stdout.write(self.style.SUCCESS("Accounting Sync Complete"))
