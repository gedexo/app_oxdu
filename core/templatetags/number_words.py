from django import template
from num2words import num2words
from decimal import Decimal

register = template.Library()

@register.filter
def in_words(value):
    """
    Convert numbers to English words.
    Handles Decimal, int, float safely.
    """
    if value is None:
        return ""

    try:
        value = int(Decimal(value))
        words = num2words(value, lang='en_IN')
        return words.replace('-', ' ').title()
    except Exception:
        return ""
