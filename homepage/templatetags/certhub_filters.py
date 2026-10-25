"""Собственные фильтры шаблонов CertHub."""
from datetime import date

from django import template

register = template.Library()


@register.filter
def ru_date(value):
    """Преобразовать дату ГГГГ-ММ-ДД из SQLite в формат ДД.ММ.ГГГГ."""
    if not value:
        return ""
    try:
        return date.fromisoformat(str(value)).strftime("%d.%m.%Y")
    except ValueError:
        return value
