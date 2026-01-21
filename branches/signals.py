from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Q
import logging

from .models import Branch
from accounting.models import Account, GroupMaster
from accounting.constants import (
    ACCOUNT_GROUP_CHOICES,
    ACCOUNT_TO_GROUP_MAPPING,
    ACCOUNT_CODE_MAPPING,
    GROUP_CATEGORIES,
    GROUP_HIERARCHY,
    CATEGORY_TO_MAIN_GROUP,
    LOCKED_ACCOUNT_CHOICES,
)

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {'Assets', 'Liabilities', 'Equity', 'Income', 'Expense'}
VALID_MAIN_GROUPS = {'balance_sheet', 'profit_and_loss', 'cash_flow', 'others'}

@receiver(post_save, sender=Branch)
def create_default_accounts_and_groups(sender, instance, created, **kwargs):
    if not created:
        return

    logger.info(f"Creating default accounting setup for branch {instance.name}")
    
    # We use a try-except block here to ensure signal failures don't crash branch creation
    try:
        with transaction.atomic():
            groups = create_account_groups(instance)
            create_default_accounts(instance, groups)
    except Exception as e:
        logger.error(f"Failed to setup accounting for branch {instance.id}: {e}")

# ---------------------------------------------------------------------
# GROUP CREATION
# ---------------------------------------------------------------------
def create_account_groups(branch):
    """
    Creates groups idempotently. Returns a dict of {code: GroupObject}.
    """
    # 1. Load existing groups to avoid re-querying inside loop
    created_groups = {
        g.code: g
        for g in GroupMaster.objects.filter(branch=branch)
    }

    all_groups = dict(ACCOUNT_GROUP_CHOICES)
    
    # Identify what needs to be created
    remaining = set(all_groups.keys()) - set(created_groups.keys())
    
    # Loop to handle hierarchy dependencies (Parent must exist before Child)
    # We loop up to 10 times to resolve deep nesting
    for _ in range(10):
        if not remaining:
            break

        progress = False
        
        # Iterate over a copy of remaining so we can modify the set
        for code in list(remaining):
            parent_code = GROUP_HIERARCHY.get(code)

            # If parent is required but not yet created, skip for now
            if parent_code and parent_code not in created_groups:
                continue

            # Validate Configuration
            category = GROUP_CATEGORIES.get(code)
            if not category or category not in VALID_CATEGORIES:
                logger.warning(f"Configuration Error: Invalid category for group {code}")
                remaining.remove(code) # Remove to prevent infinite loop
                continue

            main_group = CATEGORY_TO_MAIN_GROUP.get(category)
            if not main_group:
                logger.warning(f"Configuration Error: Invalid main group for {category}")
                remaining.remove(code)
                continue

            # Check if group exists by Name (fallback if code changed but name same)
            # This helps prevent duplicates if code logic changed slightly
            existing_by_name = GroupMaster.objects.filter(
                branch=branch, 
                name=all_groups[code]
            ).first()

            if existing_by_name:
                group = existing_by_name
                # Ensure code is normalized
                if group.code != code:
                    group.code = code
                    group.is_locked = True
                    group.locking_group = code
                    group.save()
            else:
                # Create new group
                group = GroupMaster.objects.create(
                    branch=branch,
                    code=code,
                    name=all_groups[code],
                    nature_of_group=category,
                    main_group=main_group,
                    parent=created_groups.get(parent_code),
                    is_locked=True,
                    locking_group=code,
                    description=f"System generated group: {all_groups[code]}",
                )

            created_groups[code] = group
            remaining.remove(code)
            progress = True

        if not progress:
            logger.error(f"Group hierarchy unresolved for branch {branch.id}: {remaining}")
            break

    return created_groups


# ---------------------------------------------------------------------
# ACCOUNT CREATION (FIXED)
# ---------------------------------------------------------------------
def create_default_accounts(branch, created_groups):
    created_accounts = []
    branch_code_prefix = get_branch_code(branch)

    for account_key, account_name in LOCKED_ACCOUNT_CHOICES:
        
        # 1. Determine expected Code and Group
        base_code = ACCOUNT_CODE_MAPPING.get(account_key, "99999")
        target_account_code = f"{branch_code_prefix}-{base_code}"
        
        group_code = ACCOUNT_TO_GROUP_MAPPING.get(account_key)
        group = created_groups.get(group_code)

        if not group:
            logger.warning(f"Skipping account {account_name} – missing group {group_code}")
            continue

        # 2. CHECK FOR EXISTING ACCOUNT (The Fix)
        # We check by Locking Key OR Code OR Name to prevent duplicates
        account = Account.objects.filter(
            Q(branch=branch) & 
            (Q(locking_account=account_key) | Q(code=target_account_code) | Q(name=account_name))
        ).first()

        if account:
            # Account exists, ensure it is locked correctly (Claim it)
            updated = False
            if account.locking_account != account_key:
                account.locking_account = account_key
                updated = True
            if not account.is_locked:
                account.is_locked = True
                updated = True
            
            if updated:
                account.save()
            
            continue # Skip creation

        # 3. Create New Account if absolutely not found
        # Ensure code is truly unique (in case manual accounts took the spot)
        final_code = generate_unique_account_code(branch, target_account_code)

        new_account = Account.objects.create(
            branch=branch,
            ledger_type='GENERAL',
            code=final_code,
            name=account_name,
            under=group,
            is_locked=True,
            locking_account=account_key,
        )

        created_accounts.append(new_account)

    return created_accounts


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def get_branch_code(branch):
    if hasattr(branch, 'code') and branch.code:
        return branch.code
    return f"{branch.id:03d}"  # Simplified for consistency


def generate_unique_account_code(branch, desired_code):
    """
    Checks if desired_code exists. If yes, appends suffix.
    """
    if not Account.objects.filter(branch=branch, code=desired_code).exists():
        return desired_code

    # If taken, try suffixes
    counter = 1
    while True:
        new_code = f"{desired_code}-{counter:02d}"
        if not Account.objects.filter(branch=branch, code=new_code).exists():
            return new_code
        counter += 1
        if counter > 50:
             raise ValueError(f"Unable to generate unique code for {desired_code}")

# ---------------------------------------------------------------------
# VALIDATION / REPAIR (Used by Command)
# ---------------------------------------------------------------------
def validate_branch_accounts(branch):
    # Just checks if the locked accounts exist
    required_keys = [k for k, v in LOCKED_ACCOUNT_CHOICES]
    existing_keys = Account.objects.filter(
        branch=branch, 
        locking_account__in=required_keys
    ).count()
    
    return existing_keys == len(required_keys)

def create_missing_accounts_for_branch(branch):
    with transaction.atomic():
        groups = create_account_groups(branch)
        return create_default_accounts(branch, groups)