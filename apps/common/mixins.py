from django.contrib.admin import SimpleListFilter
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------
# 1. MIXIN DE LOGGING PARA VISTAS
# ------------------------------------------------------------------------
class LoggingMixin:
    """
    Mixin para vistas basadas en clases que captura excepciones.
    Registra el error en el log y muestra un mensaje amigable al usuario.
    """
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            # Obtener nombre del modelo o de la vista
            model_name = getattr(self, 'model', None)
            if model_name:
                model_name = model_name.__name__
            else:
                model_name = self.__class__.__name__

            logger.error(f"Error en {model_name}: {str(e)}", exc_info=True)
            messages.error(
                request,
                f"Ocurrió un error inesperado en {model_name}. "
                "Por favor, revisa los datos o contacta al administrador."
            )
            redirect_url = getattr(self, 'success_url', reverse_lazy('home'))
            return redirect(redirect_url)


# ------------------------------------------------------------------------
# 2. FILTRO PARA ADMIN: BORRADOS / NO BORRADOS
# ------------------------------------------------------------------------
class DeletedAtFilterMixin(SimpleListFilter):
    """Filtro para el admin que permite mostrar registros borrados o no borrados."""
    title = 'Estado de borrado'
    parameter_name = 'deleted'

    def lookups(self, request, model_admin):
        return (
            ('no', 'No borrados'),
            ('yes', 'Borrados'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(deleted_at__isnull=True)
        elif self.value() == 'yes':
            return queryset.filter(deleted_at__isnull=False)
        return queryset


# ------------------------------------------------------------------------
# 3. MIXIN PARA ADMIN: ACCIONES MASIVAS DE BORRADO SUAVE Y RESTAURACIÓN
# ------------------------------------------------------------------------
class SoftDeleteActionsAdminMixin:
    """Añade acciones masivas de borrado suave y restauración en el admin."""
    actions = ['action_soft_delete', 'action_restore']

    def get_actions(self, request):
        actions = super().get_actions(request)
        opts = self.model._meta

        # Verificar si el modelo hereda de SoftDeleteMixin
        is_softdelete_model = any(
            base.__name__ == 'SoftDeleteMixin' for base in self.model.__mro__
        )

        if is_softdelete_model:
            # Verificar permisos de soft delete y restore
            if not (request.user.is_superuser or
                    request.user.has_perm(f"{opts.app_label}.soft_delete_{opts.model_name}")):
                actions.pop('action_soft_delete', None)

            if not (request.user.is_superuser or
                    request.user.has_perm(f"{opts.app_label}.restore_{opts.model_name}")):
                actions.pop('action_restore', None)
        else:
            # Ocultar acciones si el modelo no soporta soft delete
            actions.pop('action_soft_delete', None)
            actions.pop('action_restore', None)

        return actions

    def action_soft_delete(self, request, queryset):
        """Acción masiva: borrado suave de los registros seleccionados."""
        updated = 0
        for obj in queryset:
            if hasattr(obj, 'deleted_at') and not obj.deleted_at:
                obj.soft_delete()
                updated += 1
        self.message_user(request, f"{updated} objeto(s) borrado(s) suavemente.")
    action_soft_delete.short_description = "Borrado suave de seleccionados"

    def action_restore(self, request, queryset):
        """Acción masiva: restauración de los registros seleccionados."""
        restored = 0
        for obj in queryset:
            if hasattr(obj, 'deleted_at') and obj.deleted_at:
                obj.restore()
                restored += 1
        self.message_user(request, f"{restored} objeto(s) restaurado(s).")
    action_restore.short_description = "Restaurar seleccionados"


# ------------------------------------------------------------------------
# 4. MIXIN PARA ADMIN: FILTRO DE BORRADO Y PERMISOS
# ------------------------------------------------------------------------
class SoftDeleteAdminMixin(SoftDeleteActionsAdminMixin):
    """Admin mixin que añade el filtro de borrado y control de permisos."""
    list_filter = [DeletedAtFilterMixin]

    def get_list_filter(self, request):
        list_filter = super().get_list_filter(request)
        opts = self.model._meta

        # Si el usuario no tiene permiso de restore, ocultar el filtro de borrados
        if not (request.user.is_superuser or
                request.user.has_perm(f"{opts.app_label}.restore_{opts.model_name}")):
            if list_filter and DeletedAtFilterMixin in list_filter:
                list_filter = [f for f in list_filter if f != DeletedAtFilterMixin]

        return list_filter