import re

from .models import Account
from django.db.models import Max


def generate_account_code(branch, ledger_type=None):
    """Generate unique account code for a branch"""
    try:
        # Determine prefix based on ledger type
        prefix_map = {
            'CUSTOMER': 'CU',
            'SUPPLIER': 'SU',
            'EMPLOYEE': 'EM',
            'STAKE_HOLDER': 'SH',
            'GENERAL': 'ACC',
        }
        
        prefix = prefix_map.get(ledger_type, 'ACC')
        
        # Find the highest existing account code for this branch and prefix
        try:
            last_account = Account.objects.filter(
                branch=branch,
                code__iregex=r'^{}-\d+$'.format(re.escape(prefix))
            ).aggregate(max_code=Max('code'))

            if last_account['max_code']:
                match = re.search(r'\d+$', last_account['max_code'])
                if match:
                    new_number = int(match.group()) + 1
                else:
                    new_number = 1
            else:
                new_number = 1
        except Exception:
            new_number = 1

        return f"{prefix}-{new_number:04d}"

    except Exception as e:
        print(f"Error generating account code: {e}")
        # Fallback
        count = Account.objects.filter(branch=branch).count() + 1
        return f"ACC-{count:04d}"