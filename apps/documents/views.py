import logging
import operator
from functools import reduce
from urllib.parse import urlencode
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from common.mixins import LoggingMixin
from .models import Gazette, Document
from .forms import GazetteForm, DocumentForm  

logger = logging.getLogger(__name__)


# ==================================================
# SEARCH LIST MIXIN (Búsqueda y filtros)
# ==================================================
class SearchListMixin:
    """Mixin que añade búsqueda y filtros a las vistas de listado."""
    search_fields = []
    filter_fields = []

    def get_active_filters(self):
        active_filters = []
        raw_filters = self.request.GET.getlist('active_filter')
        for item in raw_filters:
            if '|' in item:
                field_name, value = item.split('|', 1)
                active_filters.append((field_name, value))
        filter_name = self.request.GET.get('filter')
        filter_value = self.request.GET.get('value')
        if filter_name and filter_value and not active_filters:
            active_filters.append((filter_name, filter_value))
        return active_filters

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        if query and self.search_fields:
            filters = [Q(**{f'{field}__icontains': query}) for field in self.search_fields]
            queryset = queryset.filter(reduce(operator.or_, filters))
        active_filters = self.get_active_filters()
        if active_filters:
            groups = {}
            for field_name, value in active_filters:
                groups.setdefault(field_name, []).append(value)
            for field_name, values in groups.items():
                lookup = field_name
                or_filters = [Q(**{lookup: v}) for v in values]
                if or_filters:
                    queryset = queryset.filter(reduce(operator.or_, or_filters))
        return queryset

    def build_query_string(self, additional_filters=None):
        params = {}
        query = self.request.GET.get('q', '').strip()
        if query:
            params['q'] = query
        active_filters = [f'{field}|{value}' for field, value in self.get_active_filters()]
        if additional_filters is not None:
            active_filters = additional_filters
        if active_filters:
            params['active_filter'] = active_filters
        if not params:
            return self.request.path
        return self.request.path + '?' + urlencode(params, doseq=True)

    def get_filter_tags(self):
        tags = []
        active_filters = set(self.get_active_filters())
        queryset = self.model.objects.all()
        for field_name in self.filter_fields:
            values = queryset.values_list(field_name, flat=True).distinct().order_by(field_name)
            for value in values:
                if value is None or value == '':
                    continue
                label = self.get_filter_label(field_name, value)
                active = (field_name, str(value)) in active_filters
                current_filter_key = f'{field_name}|{value}'
                if active:
                    new_filters = [item for item in active_filters if item != (field_name, str(value))]
                    new_filters = [f'{field}|{val}' for field, val in new_filters]
                else:
                    new_filters = [f'{field}|{val}' for field, val in active_filters] + [current_filter_key]
                url = self.build_query_string(additional_filters=new_filters)
                tags.append({
                    'label': label,
                    'filter': field_name,
                    'value': value,
                    'active': active,
                    'url': url,
                })
        return tags

    def get_filter_label(self, field_name, value):
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
        context['filter_tags'] = self.get_filter_tags()
        return context


# ==================================================
# VISTAS PARA GACETAS
# ==================================================
class GazetteListView(LoginRequiredMixin, SearchListMixin, ListView):
    model = Gazette
    template_name = 'documents/gazette_list.html'
    context_object_name = 'gazettes'
    paginate_by = 20
    search_fields = ['number', 'year', 'description']
    filter_fields = ['year']


class GazetteCreateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, CreateView):
    model = Gazette
    form_class = GazetteForm
    template_name = 'documents/gazette_form.html'
    success_url = reverse_lazy('documents:gazette_list')
    permission_required = 'documents.add_gazette'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para crear gacetas.")
        return redirect('documents:gazette_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Gaceta creada exitosamente.")
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class GazetteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, UpdateView):
    model = Gazette
    form_class = GazetteForm
    template_name = 'documents/gazette_form.html'
    success_url = reverse_lazy('documents:gazette_list')
    permission_required = 'documents.change_gazette'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para editar gacetas.")
        return redirect('documents:gazette_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Gaceta actualizada correctamente.")
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class GazetteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, DeleteView):
    model = Gazette
    template_name = 'documents/gazette_confirm_delete.html'
    success_url = reverse_lazy('documents:gazette_list')
    permission_required = 'documents.soft_delete_gazette'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para eliminar gacetas.")
        return redirect('documents:gazette_list')

    def form_valid(self, form):
        messages.success(self.request, "Gaceta movida a la papelera. Puedes restaurarla si lo deseas.")
        return super().form_valid(form)


class GazetteDetailView(LoginRequiredMixin, LoggingMixin, DetailView):
    model = Gazette
    template_name = 'documents/gazette_detail.html'
    context_object_name = 'gazette'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = self.object.documents.all().order_by('-emission_date')
        context['documents'] = documents
        context['total_documents'] = documents.count()
        return context


# ==================================================
# VISTAS PARA DOCUMENTOS
# ==================================================
class DocumentListView(LoginRequiredMixin, SearchListMixin, ListView):
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20
    search_fields = ['title', 'number', 'description', 'gazette__number', 'gazette__year']
    filter_fields = ['document_type__name', 'issuing_entity__name', 'is_approved']

    def get_queryset(self):
        queryset = super().get_queryset()
        year = self.request.GET.get('year')
        month = self.request.GET.get('month')
        if year:
            queryset = queryset.filter(emission_date__year=year)
        if month:
            queryset = queryset.filter(emission_date__month=month)
        return queryset


class DocumentCreateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:document_list')
    permission_required = 'documents.add_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para crear documentos.")
        return redirect('documents:document_list')

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Documento creado exitosamente.")
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:document_list')
    permission_required = 'documents.change_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para editar documentos.")
        return redirect('documents:document_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Documento actualizado correctamente.")
        return response

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class DocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, LoggingMixin, DeleteView):
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('documents:document_list')
    permission_required = 'documents.soft_delete_document'

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permiso para eliminar documentos.")
        return redirect('documents:document_list')

    def form_valid(self, form):
        messages.success(self.request, "Documento movido a la papelera. Puedes restaurarla si lo deseas.")
        return super().form_valid(form)


class DocumentDetailView(LoginRequiredMixin, LoggingMixin, DetailView):
    model = Document
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'