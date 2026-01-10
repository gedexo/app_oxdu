from .models import Employee, Partner


def generate_employee_id():
    # Filter out employees where `employee_id` is None and where the employee is inactive
    employee_ids = [int(employee.employee_id) for employee in Employee.objects.exclude(employee_id__isnull=True).filter(is_active=True)]

    # If there are no valid employee IDs, start with "0001"
    if not employee_ids:
        next_employee_id = "0001"
    else:
        # Get the maximum employee ID and increment it by 1
        max_employee_id = max(employee_ids)
        next_employee_id = str(max_employee_id + 1).zfill(4)

    return next_employee_id


def generate_partner_id():
    # Filter out partners where `partner_id` is None and where the partner is inactive
    partner_ids = [int(partner.partner_id) for partner in Partner.objects.exclude(partner_id__isnull=True).filter(is_active=True)]

    # If there are no valid partner IDs, start with "0001"
    if not partner_ids:
        next_partner_id = "0001"
    else:
        # Get the maximum partner ID and increment it by 1
        max_partner_id = max(partner_ids)
        next_partner_id = str(max_partner_id + 1).zfill(4)

    return next_partner_id