import re
from django.db import models
from .models import Account
from django.db.models import Max


def generate_account_code(ledger_type=None):
    """Generate global unique account code (order-based, not branch-wise)"""

    prefix_map = {
        'CUSTOMER': 'CU',
        'SUPPLIER': 'SU',
        'EMPLOYEE': 'EM',
        'STAKE_HOLDER': 'SH',
        'GENERAL': 'ACC',
    }

    prefix = prefix_map.get(ledger_type, 'ACC')

    # Get highest numeric part globally
    last_code = (
        Account.objects
        .filter(code__startswith=f"{prefix}-")
        .annotate(
            number=models.functions.Cast(
                models.functions.Substr('code', len(prefix) + 2),
                models.IntegerField()
            )
        )
        .aggregate(max_number=Max('number'))
    )

    next_number = (last_code['max_number'] or 0) + 1

    return f"{prefix}-{next_number:04d}"