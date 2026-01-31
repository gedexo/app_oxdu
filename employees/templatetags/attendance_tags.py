from django import template
register = template.Library()

@register.simple_tag
def define_holiday(date):
    if date.weekday() == 6:
        return True
    if date.weekday() == 5 and 8 <= date.day <= 14:
        return True
    return False