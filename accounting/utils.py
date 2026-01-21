
def get_bank_cash_account_group_ids(branch):
    """
    Returns list of GroupMaster IDs for BANK and CASH accounts for a branch
    """
    from accounting.models import GroupMaster

    return list(
        GroupMaster.objects.filter(
            locking_group__in=("BANK_ACCOUNT", "CASH_ACCOUNT"),
            branch=branch
        ).values_list("id", flat=True)
    )

def get_direct_expense_group_ids(branch):
    """
    Returns a list of GroupMaster IDs for DIRECT EXPENSES
    (including all child groups) for a branch
    """
    from accounting.models import GroupMaster

    group = GroupMaster.objects.filter(
        locking_group="DIRECT_EXPENSES",
        branch=branch
    ).first()

    if not group:
        return []

    return list(
        group.get_descendants(include_self=True)
             .values_list('id', flat=True)
    )

def get_indirect_expense_group_ids(branch):
    """
    Returns a list of GroupMaster IDs for INDIRECT EXPENSES
    (including all child groups) for a branch
    """
    from accounting.models import GroupMaster

    group = GroupMaster.objects.filter(
        locking_group="INDIRECT_EXPENSES",
        branch=branch
    ).first()

    if not group:
        return []

    return list(
        group.get_descendants(include_self=True)
             .values_list('id', flat=True)
    )

def get_direct_income_group_ids(branch):
    """
    Returns a list of GroupMaster IDs for DIRECT INCOMES
    (including all child groups) for a branch
    """
    from accounting.models import GroupMaster

    group = GroupMaster.objects.filter(
        locking_group="DIRECT_INCOME",
        branch=branch
    ).first()
    if not group:
        return []

    return list(
        group.get_descendants(include_self=True)
             .values_list('id', flat=True)
    )

def get_indirect_income_group_ids(branch):
    """
    Returns a list of GroupMaster IDs for INDIRECT INCOMES
    (including all child groups) for a branch
    """
    from accounting.models import GroupMaster

    group = GroupMaster.objects.filter(
        locking_group="INDIRECT_INCOME",
        branch=branch
    ).first()

    if not group:
        return []

    return list(
        group.get_descendants(include_self=True)
             .values_list('id', flat=True)
    )


def get_sundry_creditors_group_ids(branch):
    """
    Returns a list of GroupMaster IDs for SUNDRY CREDITORS
    (including all child groups) for a branch
    """
    from accounting.models import GroupMaster

    group = GroupMaster.objects.filter(
        locking_group="SUNDRY_CREDITORS",
        branch=branch
    ).first()

    if not group:
        return []

    return list(
        group.get_descendants(include_self=True)
             .values_list('id', flat=True)
    )


def get_sundry_debtors_group_ids(branch):
    """
    Returns a list of GroupMaster IDs for SUNDRY DEBTORS
    (including all child groups) for a branch
    """
    from accounting.models import GroupMaster

    group = GroupMaster.objects.filter(
        locking_group="SUNDRY_DEBTORS",
        branch=branch
    ).first()

    if not group:
        return []

    return list(
        group.get_descendants(include_self=True)
             .values_list('id', flat=True)
    )