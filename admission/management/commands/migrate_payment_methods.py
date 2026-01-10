from django.core.management.base import BaseCommand
from admission.models import FeeReceipt, PaymentMethod
from django.db.models import Sum
from decimal import Decimal

class Command(BaseCommand):
    help = "Migrate old FeeReceipt amounts into PaymentMethod entries"

    def handle(self, *args, **kwargs):
        receipts = FeeReceipt.objects.filter(is_active=True)

        for r in receipts:
            self.stdout.write(f"Processing Receipt: {r.id} ({r.receipt_no})")

            # Skip if already migrated
            if r.payment_methods.exists():
                self.stdout.write("  → Already has PaymentMethods. Skipping.")
                continue

            payment_type = (r.payment_type or "").lower()
            amount = r.amount or Decimal("0")

            # Create dynamic note
            note = f"Rs {amount} paid via {payment_type}"

            # Create new PaymentMethod using old single payment fields
            PaymentMethod.objects.create(
                fee_receipt=r,
                payment_type=payment_type,
                amount=amount,
                note=note
            )

            # Update total on FeeReceipt
            total = r.payment_methods.aggregate(total=Sum("amount"))["total"] or 0
            r.amount = total
            r.save()

            self.stdout.write(f"  → PaymentMethod created. Total = {total}")

        self.stdout.write(self.style.SUCCESS("✔ Migration completed successfully!"))
