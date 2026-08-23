"""
Vistas para la papelera (soft delete, restore y hard delete).
"""
import logging
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView, ListView
from django.apps import apps
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

# Modelos que pueden aparecer en la papelera
TRASH_MODELS = []

def register_trash_model(model):
    """Registra un modelo para que aparezca en la papelera."""
    if model not in TRASH_MODELS:
        TRASH_MODELS.append(model)

# Registrar modelos automáticamente
from documents.models import Gazette, Document
register_trash_model(Gazette)
register_trash_model(Document)
# Cuando agregues más modelos, solo añádelos aquí:
# from logic_users.models import User
# register_trash_model(User)


class TrashListView(LoginRequiredMixin, ListView):
    """
    Vista que muestra todos los elementos eliminados (papelera).
    Usa ListView con paginación real.
    """
    template_name = 'common/trash_list.html'
    context_object_name = 'trash_items'
    paginate_by = 20  # Paginación de 20 elementos por página

    def get_queryset(self):
        """
        Construye la lista de elementos eliminados de todos los modelos registrados.
        """
        trash_items = []
        for model in TRASH_MODELS:
            try:
                queryset = model.all_objects.filter(deleted_at__isnull=False).order_by('-deleted_at')
                for obj in queryset:
                    trash_items.append({
                        'id': obj.pk,
                        'model_name': model._meta.verbose_name,
                        'title': str(obj),
                        'deleted_at': obj.deleted_at,
                        'model_index': TRASH_MODELS.index(model),
                        'app_label': model._meta.app_label,
                        'token': f"{model._meta.app_label}|{model._meta.model_name}|{obj.pk}",  # ✅ Para bulk actions
                        'icon': 'fas fa-file',
                        'details': [],
                    })
            except Exception as e:
                logger.error(f"Error al obtener elementos de {model.__name__}: {e}")
        return trash_items

    def get_context_data(self, **kwargs):
        """
        Añade el total de elementos al contexto.
        """
        context = super().get_context_data(**kwargs)
        context['total'] = len(self.get_queryset())  # Total real de elementos
        return context


class RestoreTrashItemView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Restaura un elemento de la papelera."""
    permission_required = 'documents.restore_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para restaurar elementos.")
        return redirect('common:trash_list')

    def post(self, request, model_index, pk):
        try:
            model = TRASH_MODELS[model_index]
            obj = model.all_objects.get(pk=pk)
            obj.restore()
            messages.success(request, f'"{obj}" restaurado correctamente.')
        except IndexError:
            messages.error(request, "Modelo no encontrado.")
        except model.DoesNotExist:
            messages.error(request, "El registro no existe en la papelera.")
        except Exception as e:
            logger.error(f"Error al restaurar: {e}")
            messages.error(request, f'Error al restaurar: {e}')
        return redirect('common:trash_list')


class HardDeleteTrashItemView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Elimina permanentemente un elemento de la papelera."""
    permission_required = 'documents.delete_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para eliminar permanentemente.")
        return redirect('common:trash_list')

    def post(self, request, model_index, pk):
        try:
            model = TRASH_MODELS[model_index]
            obj = model.all_objects.get(pk=pk)
            obj.hard_delete()
            messages.success(request, f'"{obj}" eliminado definitivamente.')
        except IndexError:
            messages.error(request, "Modelo no encontrado.")
        except model.DoesNotExist:
            messages.error(request, "El registro no existe en la papelera.")
        except Exception as e:
            logger.error(f"Error al eliminar permanentemente: {e}")
            messages.error(request, f'Error al eliminar: {e}')
        return redirect('common:trash_list')


class BulkTrashActionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Acciones masivas en la papelera (restaurar o eliminar permanentemente)."""
    permission_required = 'documents.restore_document'  # Se requiere al menos restore

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para realizar acciones masivas en la papelera.")
        return redirect('common:trash_list')

    def post(self, request):
        action = request.POST.get('bulk_action')
        selected = request.POST.getlist('selected_items')

        # ============================================================
        # 1. MANEJAR "RESTAURAR TODO" Y "ELIMINAR TODO"
        # ============================================================
        if action in ['restore_all', 'delete_all']:
            # Obtener todos los elementos de la papelera
            selected = []
            for model in TRASH_MODELS:
                for obj in model.all_objects.filter(deleted_at__isnull=False):
                    selected.append(f"{model._meta.app_label}|{model._meta.model_name}|{obj.pk}")

            if not selected:
                messages.warning(request, "No hay elementos en la papelera.")
                return redirect('common:trash_list')

        # ============================================================
        # 2. VERIFICAR PERMISOS SEGÚN LA ACCIÓN
        # ============================================================
        if action in ['restore', 'restore_all'] and not request.user.has_perm('documents.restore_document'):
            messages.error(request, "No tienes permiso para restaurar elementos.")
            return redirect('common:trash_list')

        if action in ['delete', 'delete_all'] and not request.user.has_perm('documents.delete_document'):
            messages.error(request, "No tienes permiso para eliminar permanentemente.")
            return redirect('common:trash_list')

        if not selected:
            messages.warning(request, "No se seleccionaron elementos.")
            return redirect('common:trash_list')

        # ============================================================
        # 3. PROCESAR LAS ACCIONES
        # ============================================================
        restored = 0
        deleted = 0
        errors = 0

        for token in selected:
            try:
                app_label, model_name, pk = token.split('|')
                model = apps.get_model(app_label, model_name)
                obj = model.all_objects.get(pk=pk)

                if action in ['restore', 'restore_all']:
                    obj.restore()
                    restored += 1
                elif action in ['delete', 'delete_all']:
                    obj.hard_delete()
                    deleted += 1

            except ValueError:
                errors += 1
                logger.error(f"Token inválido: {token}")
            except model.DoesNotExist:
                errors += 1
                logger.error(f"Objeto no encontrado: {token}")
            except Exception as e:
                errors += 1
                logger.error(f"Error en bulk action para {token}: {e}")

        # ============================================================
        # 4. MENSAJES DE RESULTADO
        # ============================================================
        if action in ['restore', 'restore_all'] and restored > 0:
            messages.success(request, f"{restored} elemento(s) restaurado(s).")
        elif action in ['delete', 'delete_all'] and deleted > 0:
            messages.success(request, f"{deleted} elemento(s) eliminado(s) permanentemente.")

        if errors > 0:
            messages.warning(request, f"{errors} elemento(s) no pudieron procesarse.")

        return redirect('common:trash_list')