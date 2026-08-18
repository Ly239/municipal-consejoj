"""
Filtros de plantilla para verificar grupos de usuarios.
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
        """
        Verifica si el usuario pertenece a un grupo específico.
        """
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
        """
        Retorna la lista de nombres de grupos del usuario.
        """
        if not user or not user.is_authenticated:
            return []
        return list(user.groups.values_list('name', flat=True))


# ------------------------------------------------------------------------
# FILTROS PARA PLANTILLAS
# ------------------------------------------------------------------------
@register.filter(name='has_group')
def has_group(user, group_name):
    """Filtro: ¿El usuario pertenece al grupo 'group_name'?"""
    return GroupManager.user_has_group(user, group_name)


@register.filter(name='has_any_group')
def has_any_group(user, group_names):
    """Filtro: ¿El usuario pertenece a alguno de los grupos listados?"""
    return GroupManager.user_has_any_group(user, group_names)


@register.filter(name='get_groups')
def get_groups(user):
    """Filtro: Retorna los nombres de los grupos del usuario."""
    return GroupManager.get_user_groups(user)