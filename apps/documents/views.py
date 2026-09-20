"""
Vistas de la app documents

Contiene:
- SearchListMixin: búsqueda y filtros reutilizables.
- Vistas CRUD de Gazette (Gacetas).
- Vistas CRUD de Document (Documentos).
"""
import logging
import operator
from functools import reduce
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView
)

from common.mixins import LoggingMixin
from .models import Gazette, Document, DocumentType
from .forms import GazetteForm, DocumentForm

logger = logging.getLogger(__name__)


# ==================================================
# SEARCH LIST MIXIN (Búsqueda y filtros reutilizables)
# ==================================================
class SearchListMixin:
    """
    Mixin que añade búsqueda y filtros a las vistas de listado.

    Soporta:
    - Búsqueda de texto (icontains) en múltiples campos.
    - Búsqueda exacta por número cuando el término es solo dígitos.
    - Búsqueda multi-término (separado por espacios o guiones) con AND.
    - Filtros por campo con OR entre valores del mismo campo.

    Atributos configurables en las vistas hijas:
    - search_fields: campos donde buscar (texto o numéricos).
    - filter_fields: campos donde agrupar filtros por valor.
    - numeric_fields: subconjunto de search_fields que son numéricos.
    """

    search_fields = []
    filter_fields = []
    numeric_fields = []

    @cached_property
    def active_filters(self):
        """
        Filtros activos parseados del request (formato 'campo|valor').
        Cacheado para no re-parsear 3 veces por request.
        """
        filters = []
        for item in self.request.GET.getlist('active_filter'):
            if '|' in item:
                field_name, value = item.split('|', 1)
                filters.append((field_name, value))
        # Compatibilidad con formato antiguo (?filter=X&value=Y)
        filter_name = self.request.GET.get('filter')
        filter_value = self.request.GET.get('value')
        if filter_name and filter_value and not filters:
            filters.append((filter_name, filter_value))
        return filters

    def get_queryset(self):
        """Punto de entrada: aplica búsqueda y filtros."""
        queryset = super().get_queryset()
        queryset = self._apply_search(queryset)
        queryset = self._apply_filters(queryset)
        return queryset

    def _apply_search(self, queryset):
        """
        Aplica búsqueda por texto o número.
        Multi-término: separado por espacios o guiones (ej: '001-2026' o '001 2026').
        """
        query = self.request.GET.get('q', '').strip()
        if not query or not self.search_fields:
            return queryset
        # Normalizar: reemplazar guiones por espacios para soportar '001-2026'
        normalized = query.replace('-', ' ')
        terms = normalized.split()
        for term in terms:
            term_q = self._build_term_q(term)
            if term_q is not None:
                queryset = queryset.filter(term_q)
        return queryset

    def _build_term_q(self, term):
        """
        Construye un Q object (OR entre search_fields) para un término.
        - Si el término es solo dígitos → búsqueda exacta en numeric_fields.
        - Si el término es texto → icontains en campos de texto.
        """
        q_objects = []
        is_digit = term.isdigit()

        for field in self.search_fields:
            is_numeric = field in self.numeric_fields

            if is_numeric and is_digit:
                # Búsqueda exacta en campo numérico ('1' encuentra número=1)
                q_objects.append(Q(**{field: int(term)}))
            elif not is_numeric and not is_digit:
                # Búsqueda de texto en campos no numéricos
                q_objects.append(Q(**{f'{field}__icontains': term}))

        if not q_objects:
            return None
        return reduce(operator.or_, q_objects)

    def _apply_filters(self, queryset):
        """Filtros por campo: OR entre valores del mismo campo, AND entre campos."""
        if not self.active_filters:
            return queryset
        groups = {}
        for field_name, value in self.active_filters:
            groups.setdefault(field_name, []).append(value)
        for field_name, values in groups.items():
            or_filters = [Q(**{field_name: v}) for v in values]
            if or_filters:
                queryset = queryset.filter(reduce(operator.or_, or_filters))
        return queryset

    def build_query_string(self, additional_filters=None):
        """Construye query string preservando filtros activos + adicionales."""
        params = {}
        query = self.request.GET.get('q', '').strip()
        if query:
            params['q'] = query

        if additional_filters is not None:
            filters_list = additional_filters
        else:
            filters_list = [f'{f}|{v}' for f, v in self.active_filters]

        if filters_list:
            params['active_filter'] = filters_list
        if not params:
            return self.request.path
        return self.request.path + '?' + urlencode(params, doseq=True)

    @cached_property
    def filter_tags(self):
        """
        Genera los tags de filtros disponibles para el template.
        Cacheado: se calcula 1 sola vez por request.
        """
        tags = []
        try:
            active_list = self.active_filters
            active_set = set(active_list)
            queryset = self.model.objects.all()

            for field_name in self.filter_fields:
                values = (
                    queryset.values_list(field_name, flat=True)
                    .distinct()
                    .order_by(field_name)
                )
                for value in values:
                    if value is None or value == '':
                        continue
                    label = self.get_filter_label(field_name, value)
                    is_active = (field_name, str(value)) in active_set

                    if is_active:
                        # Remover el filtro actual
                        new_filters = [
                            f'{f}|{v}' for f, v in active_list
                            if not (f == field_name and str(v) == str(value))
                        ]
                    else:
                        # Agregar el filtro al final
                        new_filters = [f'{f}|{v}' for f, v in active_list]
                        new_filters.append(f'{field_name}|{value}')

                    url = self.build_query_string(additional_filters=new_filters)
                    tags.append({
                        'label': label,
                        'filter': field_name,
                        'value': value,
                        'active': is_active,
                        'url': url,
                    })
        except Exception as e:
            logger.error(f"Error en filter_tags: {e}")
        return tags

    def get_filter_label(self, field_name, value):
        """Devuelve el label legible de un valor de filtro."""
        try:
            field = self.model._meta.get_field(field_name)
            if getattr(field, 'choices', None):
                return dict(field.choices).get(value, value)
        except Exception:
            pass
        return value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['filter_tags'] = self.filter_tags
        return context


# ==================================================
# VISTAS PARA GACETAS
# ==================================================

class GazetteListView(LoginRequiredMixin, SearchListMixin, ListView):
    """Listado de gacetas con búsqueda y filtros."""
    model = Gazette
    template_name = 'documents/gazette_list.html'
    context_object_name = 'gazettes'
    paginate_by = 20
    search_fields = ['number', 'year', 'description']
    numeric_fields = ['number', 'year']
    filter_fields = ['year']


class GazetteCreateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, CreateView):
    """Crear una nueva gaceta."""
    model = Gazette
    form_class = GazetteForm
    template_name = 'documents/gazette_form.html'
    success_url = reverse_lazy('documents:gazette_list')
    permission_required = 'documents.add_gazette'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para crear gacetas.")
        return redirect('documents:gazette_list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Gaceta creada exitosamente.")
            return response
        except Exception as e:
            logger.error(f"Error al crear gaceta: {e}")
            messages.error(self.request, "Ocurrió un error al crear la gaceta.")
            return self.form_invalid(form)


class GazetteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, UpdateView):
    """Editar una gaceta existente."""
    model = Gazette
    form_class = GazetteForm
    template_name = 'documents/gazette_form.html'
    success_url = reverse_lazy('documents:gazette_list')
    permission_required = 'documents.change_gazette'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para editar gacetas.")
        return redirect('documents:gazette_list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Gaceta actualizada correctamente.")
            return response
        except Exception as e:
            logger.error(f"Error al actualizar gaceta: {e}")
            messages.error(self.request, "Ocurrió un error al actualizar la gaceta.")
            return self.form_invalid(form)


class GazetteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, DeleteView):
    """Mover una gaceta a la papelera (soft delete)."""
    model = Gazette
    template_name = 'documents/gazette_confirm_delete.html'
    success_url = reverse_lazy('documents:gazette_list')
    permission_required = 'documents.soft_delete_gazette'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para eliminar gacetas.")
        return redirect('documents:gazette_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, "Gaceta movida a la papelera. Puedes restaurarla si lo deseas.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error al eliminar gaceta: {e}")
            messages.error(self.request, "Ocurrió un error al mover la gaceta a la papelera.")
            return redirect('documents:gazette_list')


class GazetteDetailView(LoginRequiredMixin, LoggingMixin, DetailView):
    """Detalle de una gaceta con sus documentos asociados."""
    model = Gazette
    template_name = 'documents/gazette_detail.html'
    context_object_name = 'gazette'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # select_related para cargar relaciones de cada documento en 1 query
            documents = self.object.documents.select_related(
                'document_type', 'issuing_entity'
            ).order_by('-emission_date')
            context['documents'] = documents
            context['total_documents'] = documents.count()
        except Exception as e:
            logger.error(f"Error al obtener documentos de la gaceta {self.object.pk}: {e}")
            context['documents'] = []
            context['total_documents'] = 0
            messages.warning(self.request, "No se pudieron cargar los documentos asociados.")
        return context


# ==================================================
# VISTAS PARA DOCUMENTOS
# ==================================================

class DocumentListView(LoginRequiredMixin, SearchListMixin, ListView):
    """Listado de documentos con búsqueda y filtros avanzados."""
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    search_fields = [
        'title', 'description',
        'number', 'gazette__number', 'gazette__year',
        'document_type__name', 'issuing_entity__name',
    ]
    numeric_fields = ['number', 'gazette__number', 'gazette__year']
    filter_fields = ['document_type__name', 'issuing_entity__name', 'is_approved']

    def get_context_data(self, **kwargs):
        """Añade años únicos (desde emisión) y tipos de documento para los dropdowns."""
        context = super().get_context_data(**kwargs)
        try:
            # Años únicos desde emission_date (coherente con el filtro de mes)
            context['years'] = (
                Document.objects.filter(emission_date__isnull=False)
                .values_list('emission_date__year', flat=True)
                .distinct()
                .order_by('-emission_date__year')
            )
            # Tipos de documento para el dropdown
            context['document_types'] = DocumentType.objects.all()
        except Exception as e:
            logger.error(f"Error al obtener años/tipos para filtros: {e}")
            context['years'] = []
            context['document_types'] = []
        return context

    def get_queryset(self):
        """Aplicar búsqueda/filtros + filtros específicos del template (año, mes, rango, etc.)."""
        # select_related para evitar N+1 en los templates
        queryset = super().get_queryset().select_related(
            'gazette', 'document_type', 'issuing_entity', 'submitted_by'
        )

        # Filtro por año (desde emission_date, coherente con el mes)
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        if year:
            queryset = queryset.filter(emission_date__year=year)
        if month:
            queryset = queryset.filter(emission_date__month=month)

        # Filtro por rango de fechas
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(emission_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(emission_date__lte=date_to)

        # Filtro por tipo de documento
        doc_type = self.request.GET.get('doc_type')
        if doc_type:
            queryset = queryset.filter(document_type__id=doc_type)

        # Filtro por estado (combinaciones excluyentes)
        status = self.request.GET.get('status')
        if status == 'approved':
            queryset = queryset.filter(is_approved=True, is_annulled=False)
        elif status == 'pending':
            queryset = queryset.filter(is_approved=False, is_annulled=False)
        elif status == 'annulled':
            queryset = queryset.filter(is_annulled=True)

        return queryset.order_by('-emission_date__year', 'number')



class DocumentCreateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, CreateView):
    """Crear un nuevo documento."""
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:document_list')
    permission_required = 'documents.add_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para crear documentos.")
        return redirect('documents:document_list')

    def form_valid(self, form):
        try:
            form.instance.submitted_by = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, "Documento creado exitosamente.")
            return response
        except Exception as e:
            logger.error(f"Error al crear documento: {e}")
            messages.error(self.request, "Ocurrió un error al crear el documento.")
            return self.form_invalid(form)


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, UpdateView):
    """Editar un documento existente."""
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:document_list')
    permission_required = 'documents.change_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para editar documentos.")
        return redirect('documents:document_list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Documento actualizado correctamente.")
            return response
        except Exception as e:
            logger.error(f"Error al actualizar documento: {e}")
            messages.error(self.request, "Ocurrió un error al actualizar el documento.")
            return self.form_invalid(form)


class DocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, DeleteView):
    """Mover un documento a la papelera (soft delete)."""
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('documents:document_list')
    permission_required = 'documents.soft_delete_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para eliminar documentos.")
        return redirect('documents:document_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, "Documento movido a la papelera. Puedes restaurarla si lo deseas.")
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error al eliminar documento: {e}")
            messages.error(self.request, "Ocurrió un error al mover el documento a la papelera.")
            return redirect('documents:document_list')


class DocumentDetailView(LoginRequiredMixin, LoggingMixin, DetailView):
    """Detalle de un documento (con relaciones precargadas)."""
    model = Document
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'

    def get_queryset(self):
        """select_related para evitar N+1 al acceder a gazette, tipo, ente, usuario."""
        return super().get_queryset().select_related(
            'gazette', 'document_type', 'issuing_entity', 'submitted_by'
        )