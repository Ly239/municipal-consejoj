from django import template
from django.db.models import Count
from ..views import TRASH_MODELS

register = template.Library()

@register.simple_tag
def trash_count():
    """Retorna el número total de elementos en la papelera."""
    total = 0
    for model in TRASH_MODELS:
        total += model.all_objects.filter(deleted_at__isnull=False).count()
    return total