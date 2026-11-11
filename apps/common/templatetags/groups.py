"""
Filtros y tags de plantilla para verificar grupos de usuarios.
Permite controlar qué contenido se muestra según el rol del usuario.
"""
from django import template
from django.contrib.auth.models import Group

register = template.Library()


class GroupManager:
    """
    Utilidad para gestionar grupos de usuarios.
    Proporciona métodos para verificar membresía y obtener grupos.
    """

    @classmethod
    def user_has_group(cls, user, group_name):
        """Verifica si el usuario pertenece a un grupo específico."""
        if not user or not user.is_authenticated:
            return False
        return user.groups.filter(name=group_name).exists()

    @classmethod
    def user_has_any_group(cls, user, group_names):
        """
        Verifica si el usuario pertenece a alguno de los grupos dados.
        Puede recibir una lista o un string separado por comas.
        """
        if not user or not user.is_authenticated:
            return False

        if isinstance(group_names, str):
            group_names = [g.strip() for g in group_names.split(',')]

        return user.groups.filter(name__in=group_names).exists()

    @classmethod
    def get_user_groups(cls, user):
        """Retorna la lista de nombres de grupos del usuario."""
        if not user or not user.is_authenticated:
            return []
        return list(user.groups.values_list('name', flat=True))


# ------------------------------------------------------------------------
# FILTROS PARA PLANTILLAS
# ------------------------------------------------------------------------
@register.filter(name='has_any_group')
def has_any_group(user, group_names):
    """Filtro: ¿El usuario pertenece a alguno de los grupos listados?"""
    return GroupManager.user_has_any_group(user, group_names)


@register.filter(name='get_groups')
def get_groups(user):
    """Filtro: Retorna los nombres de los grupos del usuario."""
    return GroupManager.get_user_groups(user)


# FIX — 16-10-2026 ------------------------------------------------
# Filtro alias de `has_group` para compatibilidad con plantillas legacy
# que usan la sintaxis de filtro: {{ user|has_group:"Administrator" }}
#
# Contexto:
#   - El `simple_tag` homónimo (más abajo) cubre la sintaxis:
#         {% has_group user "Administrator" as is_admin %}
#   - Ambos registros conviven para no romper plantillas existentes.
#
# Plantillas que dependen del filtro (bug latente detectado con grep):
#   - templates/core/dashboard.html (2 usos)
#   - templates/core/includes/_navbar_private.html (1 uso)
#   - templates/documents/document_form.html (1 uso, latente)
#
# Post-entrega: unificar a una sola sintaxis (simple_tag preferido).
# ------------------------------------------------------------------------
@register.filter(name='has_group')
def has_group_filter(user, group_name):
    """
    Alias de filtro para `has_group`.
    Uso: {{ user|has_group:"Administrator" }}
    """
    return GroupManager.user_has_group(user, group_name)


# ------------------------------------------------------------------------
# SIMPLE TAGS (Evaluación segura sin errores en {% if %})
# ------------------------------------------------------------------------
@register.simple_tag(name='has_group')
def has_group(user, group_name):
    """
    Simple Tag: Permite evaluar si el usuario pertenece a un grupo sin romper el parser de Django.
    Uso en plantillas:
        {% has_group user "Administrator" as is_admin %}
        {% if is_admin %} ... {% endif %}
    """
    return GroupManager.user_has_group(user, group_name)