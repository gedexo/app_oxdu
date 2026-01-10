# branches/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
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

    logger.info("Creating default accounting setup for branch %s", instance.name)

    with transaction.atomic():
        groups = create_account_groups(instance)
        create_default_accounts(instance, groups)


# ---------------------------------------------------------------------
# GROUP CREATION
# ---------------------------------------------------------------------
def create_account_groups(branch):
    created_groups = {
        g.code: g
        for g in GroupMaster.objects.filter(branch=branch)
    }

    all_groups = dict(ACCOUNT_GROUP_CHOICES)
    remaining = set(all_groups.keys()) - set(created_groups.keys())

    for _ in range(10):  # prevent infinite loops
        if not remaining:
            break

        progress = False

        for code in list(remaining):
            parent_code = GROUP_HIERARCHY.get(code)

            if parent_code and parent_code not in created_groups:
                continue

            category = GROUP_CATEGORIES.get(code)
            if category not in VALID_CATEGORIES:
                logger.warning("Invalid category for group %s", code)
                remaining.remove(code)
                continue

            main_group = CATEGORY_TO_MAIN_GROUP.get(category)
            if main_group not in VALID_MAIN_GROUPS:
                logger.warning("Invalid main group for %s", code)
                remaining.remove(code)
                continue

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
            logger.error("Group hierarchy unresolved: %s", remaining)
            break

    return created_groups


# ---------------------------------------------------------------------
# ACCOUNT CREATION
# ---------------------------------------------------------------------
def create_default_accounts(branch, created_groups):
    created_accounts = []

    existing_keys = set(
        Account.objects.filter(
            branch=branch,
            locking_account__isnull=False
        ).values_list('locking_account', flat=True)
    )

    for account_key, account_name in LOCKED_ACCOUNT_CHOICES:
        if account_key in existing_keys:
            continue

        group_code = ACCOUNT_TO_GROUP_MAPPING.get(account_key)
        group = created_groups.get(group_code)

        if not group:
            logger.warning(
                "Skipping account %s – missing group %s",
                account_name,
                group_code
            )
            continue

        base_code = ACCOUNT_CODE_MAPPING.get(account_key, "99999")
        account_code = generate_unique_account_code(
            branch,
            f"{get_branch_code(branch)}-{base_code}"
        )

        account = Account.objects.create(
            branch=branch,
            ledger_type='GENERAL',
            code=account_code,
            name=account_name,
            under=group,
            is_locked=True,
            locking_account=account_key,
        )

        created_accounts.append(account)

    return created_accounts


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def get_branch_code(branch):
    if hasattr(branch, 'code') and branch.code:
        return branch.code
    return f"BR{branch.id:03d}"


def generate_unique_account_code(branch, base_code, max_attempts=50):
    code = base_code
    counter = 1

    while Account.objects.filter(branch=branch, code=code).exists():
        if counter > max_attempts:
            raise ValueError("Unable to generate unique account code")
        code = f"{base_code}-{counter:02d}"
        counter += 1

    return code


# ---------------------------------------------------------------------
# VALIDATION / REPAIR
# ---------------------------------------------------------------------
def validate_branch_accounts(branch):
    existing_groups = set(
        GroupMaster.objects.filter(branch=branch)
        .values_list('code', flat=True)
    )

    existing_accounts = set(
        Account.objects.filter(
            branch=branch,
            locking_account__isnull=False
        ).values_list('locking_account', flat=True)
    )

    missing_groups = [
        code for code, _ in ACCOUNT_GROUP_CHOICES
        if code not in existing_groups
    ]

    missing_accounts = [
        key for key, _ in LOCKED_ACCOUNT_CHOICES
        if key not in existing_accounts
    ]

    return not missing_groups and not missing_accounts


def create_missing_accounts_for_branch(branch):
    with transaction.atomic():
        groups = create_account_groups(branch)
        return create_default_accounts(branch, groups)
