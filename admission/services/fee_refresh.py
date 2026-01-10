from django.db import transaction
from admission.models import Admission

def refresh_fee_structure_for_student(student: Admission):
    """
    Safely refresh fee structure for a single student
    """
    if student.fee_type in ["installment", "one_time", "finance"]:
        with transaction.atomic():
            student.create_fee_structure()


def refresh_fee_structure_queryset(queryset):
    """
    Bulk refresh fee structures
    """
    count = 0
    for student in queryset.iterator():
        refresh_fee_structure_for_student(student)
        count += 1
    return count
