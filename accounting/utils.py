from django.db import transaction
from django.db.models import Sum
from transactions.models import TransactionEntry

from accounting.models import Account, GroupMaster
from accounting.constants import ACCOUNT_CODE_MAPPING, ACCOUNT_TO_GROUP_MAPPING, LOCKED_ACCOUNT_CHOICES

def get_system_account(branch, account_key):
    """
    Get or Create a System Account based on fixed keys.
    """
    if account_key not in ACCOUNT_CODE_MAPPING:
        return None

    code = ACCOUNT_CODE_MAPPING[account_key]
    
    # 1. Try to find existing account
    account = Account.objects.filter(branch=branch, code=code).first()
    if account:
        return account

    # 2. Create Group if missing
    group_code = ACCOUNT_TO_GROUP_MAPPING.get(account_key)
    # Determine main group based on account type (Assets vs Income)
    main_group = 'profit_and_loss' if 'FEE' in account_key or 'INCOME' in account_key else 'balance_sheet'
    
    group, _ = GroupMaster.objects.get_or_create(
        branch=branch,
        code=group_code,
        defaults={
            'name': group_code.replace('_', ' ').title(),
            'nature_of_group': 'Income' if main_group == 'profit_and_loss' else 'Assets',
            'main_group': main_group,
            'is_locked': True
        }
    )

    # 3. Create Account
    name = dict(LOCKED_ACCOUNT_CHOICES).get(account_key, account_key.replace('_', ' ').title())
    
    account = Account.objects.create(
        branch=branch,
        code=code,
        name=name,
        under=group,
        ledger_type='GENERAL',
        is_locked=True,
        locking_account=account_key
    )
    return account



def update_account_balance(account):
    """
    Recalculates and updates the current balance for an account based on all its transaction entries.
    Handles both DR and CR balance types correctly.
    
    Args:
        account (Account): The account to update
    """
    with transaction.atomic():
        try:
            # Lock the account for update to prevent race conditions
            account = Account.objects.select_for_update().get(pk=account.pk)
            
            # Get all entries for this account
            entries_aggregate = TransactionEntry.objects.filter(
                account=account
            ).aggregate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount')
            )
            
            total_debit = entries_aggregate['total_debit'] or 0
            total_credit = entries_aggregate['total_credit'] or 0
            
            # Calculate net balance based on account type
            if account.balance_type == 'DR':
                new_balance = (account.opening_balance + total_debit) - total_credit
            else:  # CR balance type
                new_balance = (account.opening_balance + total_credit) - total_debit
            
            # Update only if balance has changed
            if account.current_balance != new_balance:
                Account.objects.filter(pk=account.pk).update(current_balance=new_balance)
                account.refresh_from_db()
                
            return new_balance
            
        except Account.DoesNotExist:
            # Account was deleted, nothing to update
            return None
        except Exception as e:
            # Log error and re-raise
            print(f"Error updating balance for account {account.id}: {str(e)}")
            raise

def update_account_balances(account_ids):
    """
    Bulk update balances for multiple accounts.
    More efficient than updating accounts one by one.
    
    Args:
        account_ids (list): List of account IDs to update
    """
    from django.db.models import F
    
    with transaction.atomic():
        try:
            # Get all accounts at once
            accounts = Account.objects.filter(id__in=account_ids).select_for_update()
            
            # Create a mapping of account balances
            balance_updates = {}
            entries = TransactionEntry.objects.filter(account_id__in=account_ids)
            
            # Aggregate all entries for these accounts
            for entry in entries.values('account').annotate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount')
            ):
                account_id = entry['account']
                total_debit = entry['total_debit'] or 0
                total_credit = entry['total_credit'] or 0
                
                balance_updates[account_id] = {
                    'total_debit': total_debit,
                    'total_credit': total_credit
                }
            
            # Prepare bulk update
            accounts_to_update = []
            for account in accounts:
                totals = balance_updates.get(account.id, {'total_debit': 0, 'total_credit': 0})
                
                if account.balance_type == 'DR':
                    new_balance = (account.opening_balance + totals['total_debit']) - totals['total_credit']
                else:
                    new_balance = (account.opening_balance + totals['total_credit']) - totals['total_debit']
                
                if account.current_balance != new_balance:
                    account.current_balance = new_balance
                    accounts_to_update.append(account)
            
            # Bulk update
            if accounts_to_update:
                Account.objects.bulk_update(accounts_to_update, ['current_balance'])
                
            return len(accounts_to_update)
            
        except Exception as e:
            print(f"Error in bulk balance update: {str(e)}")
            raise