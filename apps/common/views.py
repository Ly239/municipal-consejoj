"""
Vistas para la papelera (soft delete, restore y hard delete).
"""
import logging
from django.db.models import ProtectedError #Mensaje claro en español
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.views import View
from django.views.generic import ListView
from django.apps import apps

logger = logging.getLogger(__name__)


# Modelos que pueden aparecer en la papelera
TRASH_MODELS = []

def register_trash_model(model):
    """Registra un modelo para que aparezca en la papelera."""
    if model not in TRASH_MODELS:
        TRASH_MODELS.append(model)

# NOTA: el registro de modelos ya NO se hace aquí con imports directos
# (from documents.models import ...) porque eso provocaba un import
# circular entre common <-> documents al arrancar Django.
# Ahora el registro ocurre en common/apps.py -> CommonConfig.ready(),
# que se ejecuta una sola vez cuando TODOS los modelos ya están
# cargados en el App Registry. Ahí se detectan automáticamente todos
# los modelos que heredan de BaseModel, así que no hace falta tocar
# este archivo cuando se agregue un modelo nuevo (ej. User).



class TrashListView(LoginRequiredMixin, ListView):
    """
    Vista que muestra todos los elementos eliminados (papelera).
    Usa ListView con paginación real.

    Filtra por key de dominio (nombre, cédula, número de gaceta/documento).
    """
    template_name = 'common/trash_list.html'
    context_object_name = 'trash_items'
    paginate_by = 20 # Paginación de 20 elementos por página

    def get_queryset(self):
        """
        Construye la lista de elementos eliminados de todos los modelos registrados.
        Si hay un query param 'q', filtra por texto libre en la key de dominio.
        """
        trash_items = []
        query = self.request.GET.get('q', '').strip().lower()

        for model in TRASH_MODELS:
            try:
                queryset = model.all_objects.filter(
                    deleted_at__isnull=False
                ).order_by('-deleted_at')

                for obj in queryset:
                    # Construir texto searchable (key de dominio)
                    search_parts = [str(obj).lower()]

                    # User → cédula
                    if hasattr(obj, 'id_number') and obj.id_number:
                        search_parts.append(str(obj.id_number).lower())

                    # Gazette / Document → número
                    if hasattr(obj, 'number') and obj.number is not None:
                        search_parts.append(f"{obj.number:03d}")
                        search_parts.append(str(obj.number))

                    search_text = ' '.join(search_parts)

                    # Filtrar si hay query
                    if query and query not in search_text:
                        continue

                    trash_items.append({
                        'id': obj.pk,
                        'model_name': model._meta.verbose_name,
                        'title': str(obj),
                        'deleted_at': obj.deleted_at,
                        'model_index': TRASH_MODELS.index(model),
                        'app_label': model._meta.app_label,
                        'token': f"{model._meta.app_label}|{model._meta.model_name}|{obj.pk}",
                        'icon': 'fas fa-file',
                        'details': [],
                    })
            except Exception as e:
                logger.error(f"Error al obtener elementos de {model.__name__}: {e}")
        return trash_items

    def get_context_data(self, **kwargs):
        """Añade total y search_query al contexto."""
        context = super().get_context_data(**kwargs)
        context['total'] = len(self.get_queryset()) # Total real de elementos
        context['search_query'] = self.request.GET.get('q', '') 
        return context



class RestoreTrashItemView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Restaura un elemento de la papelera."""

    def dispatch(self, request, *args, **kwargs):
        """Valida el model_index ANTES de que PermissionRequiredMixin lo use."""
        model_index = kwargs.get('model_index')
        if model_index is None or model_index < 0 or model_index >= len(TRASH_MODELS):
            messages.error(request, "Modelo no encontrado.")
            return redirect('common:trash_list')
        return super().dispatch(request, *args, **kwargs)

    def get_permission_required(self):
        """Calcula el permiso requerido dinámicamente según el modelo real
        (en vez de dejarlo fijo en 'documents.restore_document').
        Así funciona igual para Document, Gazette, o el futuro User."""
        model = TRASH_MODELS[self.kwargs['model_index']]
        permission_name = model.get_restore_permission_name()
        return (f"{model._meta.app_label}.{permission_name}",)

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
        except ObjectDoesNotExist:
            messages.error(request, "El registro no existe en la papelera.")
        except Exception as e:
            logger.error(f"Error al restaurar: {e}")
            messages.error(request, f'Error al restaurar: {e}')
        return redirect('common:trash_list')



class HardDeleteTrashItemView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Elimina permanentemente un elemento de la papelera.

    dispatch valida el model_index antes que PermissionRequiredMixin.
    catcha ProtectedError con mensaje amigable.
    """

    def dispatch(self, request, *args, **kwargs):
        """B69: valida el model_index ANTES de que PermissionRequiredMixin lo use."""
        model_index = kwargs.get('model_index')
        if model_index is None or model_index < 0 or model_index >= len(TRASH_MODELS):
            messages.error(request, "Modelo no encontrado.")
            return redirect('common:trash_list')
        return super().dispatch(request, *args, **kwargs)

    def get_permission_required(self):
        model = TRASH_MODELS[self.kwargs['model_index']]
        return (f"{model._meta.app_label}.delete_{model._meta.model_name}",)

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

        except ObjectDoesNotExist:
            messages.error(request, "El registro no existe en la papelera.")

        except ProtectedError:
            # Mensaje amigable cuando hay dependencias con PROTECT
            messages.error(
                request,
                f'No se puede eliminar "{obj}" porque tiene registros asociados. '
                'Eliminá primero sus dependencias (documentos, etc.).'
            )

        except Exception as e:
            logger.error(f"Error al eliminar permanentemente: {e}")
            messages.error(request, f'Error al eliminar: {e}')

        return redirect('common:trash_list')
        
        
  
class BulkTrashActionView(LoginRequiredMixin, View):
    """Acciones masivas en la papelera (restaurar o eliminar permanentemente).

    Usa ObjectDoesNotExist genérico.
    Si action es restore_all/delete_all Y hay selección, solo procesa
         los seleccionados. Si no hay selección, procesa todo.
    """

    def post(self, request):
        action = request.POST.get('bulk_action')
        selected = request.POST.getlist('selected_items')

        #Si action es restore_all/delete_all y hay selección,
        # normalizamos a restore/delete para procesar solo los seleccionados.
        if action in ['restore_all', 'delete_all'] and selected:
            action = action.replace('_all', '')

        #Si action es restore_all/delete_all y NO hay selección,
        # procesamos todo.
        if action in ['restore_all', 'delete_all'] and not selected:
            selected = []
            for model in TRASH_MODELS:
                for obj in model.all_objects.filter(deleted_at__isnull=False):
                    selected.append(f"{model._meta.app_label}|{model._meta.model_name}|{obj.pk}")

            if not selected:
                messages.warning(request, "No hay elementos en la papelera.")
                return redirect('common:trash_list')

        if not selected:
            messages.warning(request, "No se seleccionaron elementos.")
            return redirect('common:trash_list')

        restored = 0
        deleted = 0
        errors = 0
        denied = 0 # Cuenta los que se saltaron por falta de permiso

        for token in selected:
            try:
                app_label, model_name, pk = token.split('|')
                model = apps.get_model(app_label, model_name)
                obj = model.all_objects.get(pk=pk)

                if action in ['restore', 'restore_all']:
                    perm = f"{app_label}.{model.get_restore_permission_name()}"
                    if not request.user.has_perm(perm):
                        denied += 1
                        continue
                    obj.restore()
                    restored += 1

                elif action in ['delete', 'delete_all']:
                    perm = f"{app_label}.delete_{model_name}"
                    if not request.user.has_perm(perm):
                        denied += 1
                        continue
                    obj.hard_delete()
                    deleted += 1

            except ValueError:
                errors += 1
                logger.error(f"Token inválido: {token}")
            except ObjectDoesNotExist:
                errors += 1
                logger.error(f"Objeto no encontrado: {token}")
            except Exception as e:
                errors += 1
                logger.error(f"Error en bulk action para {token}: {e}")

        if restored > 0:
            messages.success(request, f"{restored} elemento(s) restaurado(s).")
        if deleted > 0:
            messages.success(request, f"{deleted} elemento(s) eliminado(s) permanentemente.")
        if denied > 0:
            messages.warning(request, f"{denied} elemento(s) no se procesaron por falta de permiso.")
        if errors > 0:
            messages.warning(request, f"{errors} elemento(s) no pudieron procesarse.")

        return redirect('common:trash_list')
