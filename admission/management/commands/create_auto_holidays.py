# management/commands/create_auto_holidays.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from masters.models import Holiday
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Create automatic holiday records for weekends'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days to look ahead for auto holidays'
        )

    def handle(self, *args, **options):
        days_ahead = options['days']
        today = timezone.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        created_count = 0
        current_date = today
        
        while current_date <= end_date:
            is_auto_holiday, holiday_name = Holiday.is_auto_holiday(current_date)
            if is_auto_holiday:
                holiday, created = Holiday.objects.get_or_create(
                    date=current_date,
                    is_auto_holiday=True,
                    defaults={
                        'name': holiday_name,
                        'scope': 'all',
                        'description': f'Auto-generated holiday: {holiday_name}'
                    }
                )
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created auto holiday: {holiday_name} on {current_date}')
                    )
            
            current_date += timedelta(days=1)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} auto holidays')
        )