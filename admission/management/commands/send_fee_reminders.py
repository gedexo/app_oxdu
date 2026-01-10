from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from admission.models import FeeStructure
from admission.utils import send_sms

class Command(BaseCommand):
    help = "Send monthly fee reminders and warnings to parents"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # --- 1️⃣ Send reminder on 1st of every month ---
        if today.day == 1:
            fee_structures = FeeStructure.objects.filter(
                payment_date__month=today.month,
                payment_date__year=today.year,
                is_paid=False,
                student__is_active=True
            )

            for fs in fee_structures:
                student = fs.student
                parent_number = student.parent_whatsapp_number or student.parent_contact_number
                if not parent_number:
                    continue

                message = (
                    f"Dear Parent,\n\n"
                    f"This is a reminder for {student.fullname()}'s fee payment.\n"
                    f"Installment: {fs.name}\n"
                    f"Amount: ₹{fs.amount}\n"
                    f"Payment Date: {fs.payment_date}\n"
                    f"Due Date: {fs.due_date}\n\n"
                    f"Please ensure payment before the due date to avoid penalties.\n"
                    f"Thank you."
                )

                send_sms(parent_number, message)
                print(f"✅ Reminder sent to {student.fullname()} ({parent_number})")

        # --- 2️⃣ Send warning if due date is passed ---
        overdue_structures = FeeStructure.objects.filter(
            due_date__lt=today,
            is_paid=False,
            student__is_active=True
        )

        for fs in overdue_structures:
            student = fs.student
            parent_number = student.parent_whatsapp_number or student.parent_contact_number
            if not parent_number:
                continue

            days_overdue = (today - fs.due_date).days
            message = (
                f"⚠️ Fee Overdue Alert ⚠️\n\n"
                f"Dear Parent,\n\n"
                f"{student.fullname()}'s installment '{fs.name}' was due on {fs.due_date}.\n"
                f"Amount: ₹{fs.amount}\n"
                f"Days Overdue: {days_overdue}\n\n"
                f"Please clear the payment immediately to avoid penalties."
            )

            send_sms(parent_number, message)
            print(f"⚠️ Warning sent to {student.fullname()} ({parent_number})")
