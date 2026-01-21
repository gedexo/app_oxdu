from django.core.management.base import BaseCommand
from masters.models import State


class Command(BaseCommand):
    help = "Load all Indian states and union territories"

    def handle(self, *args, **options):
        states = [
            "Andhra Pradesh",
            "Arunachal Pradesh",
            "Assam",
            "Bihar",
            "Chhattisgarh",
            "Goa",
            "Gujarat",
            "Haryana",
            "Himachal Pradesh",
            "Jharkhand",
            "Karnataka",
            "Kerala",
            "Madhya Pradesh",
            "Maharashtra",
            "Manipur",
            "Meghalaya",
            "Mizoram",
            "Nagaland",
            "Odisha",
            "Punjab",
            "Rajasthan",
            "Sikkim",
            "Tamil Nadu",
            "Telangana",
            "Tripura",
            "Uttar Pradesh",
            "Uttarakhand",
            "West Bengal",

            # Union Territories
            "Andaman and Nicobar Islands",
            "Chandigarh",
            "Dadra and Nagar Haveli and Daman and Diu",
            "Delhi",
            "Jammu and Kashmir",
            "Ladakh",
            "Lakshadweep",
            "Puducherry",
        ]

        created_count = 0

        for state in states:
            obj, created = State.objects.get_or_create(name=state)
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Indian states loaded successfully. New records: {created_count}"
            )
        )
