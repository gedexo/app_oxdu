from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from branches.models import Branch
from accounting.models import Account
from accounting.constants import LOCKED_ACCOUNT_CHOICES

class Command(BaseCommand):
    help = "Merges duplicate accounts within branches and cleans up data"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Starting duplicate account scan...")
        
        branches = Branch.objects.all()
        total_merged = 0
        
        for branch in branches:
            # Loop through the specific system accounts we know cause issues
            for key, name in LOCKED_ACCOUNT_CHOICES:
                self.process_duplicates(branch, key, name)
                
        self.stdout.write(self.style.SUCCESS(f"\n✨ Cleanup complete."))

    def process_duplicates(self, branch, key, name):
        """
        Finds accounts with the same name/key in a branch.
        Keeps one, merges data from others to it, and deletes the others.
        """
        # Find all accounts that look like this system account
        # We check by Name OR Key (since some duplicates might be missing the key)
        accounts = list(Account.objects.filter(
            branch=branch,
            name__iexact=name  # Case insensitive match
        ).order_by('id'))

        if len(accounts) <= 1:
            return

        self.stdout.write(f"\n👉 Branch: {branch.name} | Account: {name}")
        self.stdout.write(f"   Found {len(accounts)} copies. Merging...")

        # 1. Determine the 'Winner' (Master Account)
        # Priority: Has locking_key > Oldest ID
        master_account = None
        
        # Try to find one that already has the lock key
        for acc in accounts:
            if acc.locking_account == key:
                master_account = acc
                break
        
        # If none have the key, pick the first one (oldest)
        if not master_account:
            master_account = accounts[0]

        # 2. Separate the 'Losers'
        duplicates = [acc for acc in accounts if acc.id != master_account.id]

        with transaction.atomic():
            # Ensure master has the correct settings
            master_account.locking_account = key
            master_account.is_locked = True
            master_account.save()

            for duplicate in duplicates:
                self.merge_accounts(master_account, duplicate)

    def merge_accounts(self, master, duplicate):
        """
        Moves all relationships from duplicate to master, then deletes duplicate.
        """
        # introspect all relationships (Reverse Foreign Keys)
        # This automatically finds JournalEntries, Invoices, Payments, etc.
        links = [
            f for f in Account._meta.get_fields()
            if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
        ]

        for link in links:
            related_name = link.get_accessor_name()
            
            # Get all objects pointing to the duplicate
            try:
                # e.g. duplicate.journalentry_set.all()
                related_objects = getattr(duplicate, related_name).all()
                
                count = related_objects.count()
                if count > 0:
                    self.stdout.write(f"   ↳ Moving {count} {link.name} records to Master ID {master.id}")
                    # Update the Foreign Key to point to Master
                    # We use .update() for efficiency
                    filter_kwargs = {link.field.name: duplicate}
                    getattr(duplicate, related_name).filter(**filter_kwargs).update(**{link.field.name: master})
            except Exception as e:
                # Sometimes relations aren't standard querysets, skip if needed
                self.stdout.write(self.style.WARNING(f"   ⚠️ Could not merge {related_name}: {e}"))

        # Finally, delete the duplicate
        self.stdout.write(self.style.ERROR(f"   🗑 Deleting duplicate ID {duplicate.id} ({duplicate.code})"))
        duplicate.delete()