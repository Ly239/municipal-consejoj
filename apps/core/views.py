"""
Copyright [2026] [Proyecto universitario - Concejo Municipal de Junín]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Standard library
import logging
from types import SimpleNamespace

# Django
from django.shortcuts import render, redirect
from django.db.models import Q, ProtectedError
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone, translation
from django.utils.formats import date_format
from django.utils.html import strip_tags

# Apps externas
from documents.models import Document, Gazette

# Core local
from .models import (
    BaseContent, News, Chronicle, Councilor, AboutUs,
    Activity, Announcement, Consultation, Event, Downloadable,
    Category, Commission, Legislature, Legislator
)
# Importamos todos los formularios correctamente
from .forms import (
    NewsForm, ChronicleForm, CategoryForm, CommissionForm, CouncilorForm,
    LegislatureForm, AboutUsForm, ActivityForm, AnnouncementForm,
    ConsultationForm, EventForm, DownloadableForm
)

User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================
# MIXIN DE PERMISOS
# ============================================================

class CanEditHomeMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'core.can_edit_home'
    raise_exception = True

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "No tienes permisos para gestionar el contenido del Home.")
        return redirect('core:home')


# ============================================================
# DATOS ESTÁTICOS DE RESPALDO
# ============================================================

NEWS_DATA = [
    {
        'id': 1, 'title': 'Concejo Municipal fortalece labores de rescate', 
        'description': 'En el marco de la Sesión Ordinaria...', 
        'image': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800', 
        'date': '20 de agosto de 2026', 'category': 'Social',
    },
    {
        'id': 2, 'title': 'Nueva ordenanza para la protección del medio ambiente', 
        'description': 'El Concejo Municipal aprobó la ordenanza...', 
        'image': 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800', 
        'date': '18 de agosto de 2026', 'category': 'Cultura',
    },
    {
        'id': 3, 'title': 'Jornada de atención al ciudadano en Rubio', 
        'description': 'Jornada integral de atención ciudadana...', 
        'image': 'https://images.unsplash.com/photo-1573164713988-8665fc963095?w=800', 
        'date': '15 de agosto de 2026', 'category': 'Salud',
    },
]

SYNDICATE_DATA = [
    {'name': 'Abogado por designar', 'position': 'Síndico Procurador Municipal', 'image': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=400'},
    {'name': 'Daymar C.', 'position': 'Secretaria Municipal del Concejo', 'image': 'https://images.unsplash.com/photo-1580894732444-8ecded7900cd?w=400'},
]

ABOUT_US_DATA = {
    'who_we_are': 'El Concejo Municipal del Municipio Junín es un órgano colegiado...',
    'mission': 'Ejercer la función legislativa municipal mediante la creación...',
    'vision': 'Ser una institución legislativa de vanguardia, transparente...',
    'image_main': 'core/img/quienes_somos_junin.jpg'
}

# ============================================================
# 1. PANEL DE CONTROL Y PORTAL PÚBLICO
# ============================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['total_documents'] = Document.objects.count()
            context['total_gazettes'] = Gazette.objects.count()
            context['total_users'] = User.objects.count()
        except Exception as e:
            logger.error(f"Error Dashboard: {e}")

        try:
            from common.views import TRASH_MODELS
            trash_count = 0
            for model in TRASH_MODELS:
                if hasattr(model, 'all_objects') and hasattr(model, 'deleted_at'):
                    trash_count += model.all_objects.filter(deleted_at__isnull=False).count()
            context['total_trash'] = trash_count
        except Exception: context['total_trash'] = 0

        try:
            context['recent_documents'] = Document.objects.select_related('document_type', 'gazette').order_by('-created_at')[:5]
            context['approved_count'] = Document.objects.filter(is_approved=True, is_annulled=False).count()
            context['pending_count'] = Document.objects.filter(is_approved=False, is_annulled=False).count()
            context['annulled_count'] = Document.objects.filter(is_annulled=True).count()
        except Exception: pass
        return context


# ============================================================
# PORTAL PÚBLICO
# ============================================================

def _format_spanish_date(value):
    """
    Devuelve una fecha en español (ej. '9 de noviembre de 2026 a las 5:50 p.m.').
    sin importar el idioma configurado en settings.LANGUAGE_CODE.
    """
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    with translation.override('es'):
        # Agregamos el formato de hora: \a \l\a\s (a las) g:i a (5:50 p.m.)
        return date_format(value, 'j \\d\\e F \\d\\e Y \\a \\l\\a\\s g:i a')



def _build_slide(news):
    """
    Convierte UNA noticia en un diccionario con las mismas claves,
    venga de la base de datos (objeto News) o de los datos de respaldo
    (diccionario NEWS_DATA). Así la plantilla no necesita condicionales.

    Claves devueltas: id, title, description, image_url, date
    """
    # Caso 1: dato estático de respaldo (ya trae la fecha formateada)
    if isinstance(news, dict):
        return {
            'id': news['id'],
            'title': news['title'],
            'description': news['description'],
            'image_url': news.get('image', ''),
            'date': news['date'],
        }

    # Caso 2: noticia real de la base de datos
    # La imagen es un ImageField: se usa .url (si no hay archivo, queda vacío
    # y la plantilla mostrará la imagen por defecto).
    image_url = news.image.url if news.image else ''
    text = strip_tags(news.summary or news.content or '')
    return {
        'id': news.pk,
        'title': news.title,
        'description': text,
        'image_url': image_url,
        'date': _format_spanish_date(news.created_at),  # created_at, no publication_date
    }


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Red de seguridad: el carrusel SIEMPRE tiene diapositivas,
        # aunque algo falle más abajo.
        context['carousel_slides'] = [_build_slide(n) for n in NEWS_DATA]

        try:
            published_news = News.objects.filter(
                is_active=True, status=BaseContent.Status.PUBLISHED
            ).order_by('-created_at')

            # UNA sola consulta (antes: exists() + slice = dos consultas)
            latest = list(published_news[:3])
            if latest:
                context['carousel_slides'] = [_build_slide(n) for n in latest]

            # Se mantiene por compatibilidad con otras partes del Home
            context['news_list'] = latest if latest else NEWS_DATA

            context['chronicles'] = Chronicle.objects.filter(
                is_active=True, status=BaseContent.Status.PUBLISHED
            ).order_by('-created_at')[:3]
            context['consultations'] = Consultation.objects.filter(
                is_active=True, status=BaseContent.Status.PUBLISHED
            ).order_by('-start_date')[:3]
            context['councilors'] = Councilor.objects.filter(
                is_active=True, status=BaseContent.Status.PUBLISHED
            ).order_by('order')
            context['documentos_destacados'] = Document.objects.select_related(
                'gazette', 'document_type'
            ).order_by('-emission_date')[:2]
        except Exception as e:
            logger.error(f"Error Home: {e}")
        return context



class AboutUsView(TemplateView):
    template_name = 'core/about_us.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            about_items = AboutUs.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED)
            context['about_data'] = {
                'who_we_are': about_items.filter(slug='quienes-somos').first().content if about_items.filter(slug='quienes-somos').exists() else ABOUT_US_DATA['who_we_are'],
                'mission': about_items.filter(slug='mision').first().content if about_items.filter(slug='mision').exists() else ABOUT_US_DATA['mission'],
                'vision': about_items.filter(slug='vision').first().content if about_items.filter(slug='vision').exists() else ABOUT_US_DATA['vision'],
                'image_main': ABOUT_US_DATA['image_main']
            }
            context['legislatures'] = Legislature.objects.prefetch_related('members').all()
        except Exception: context['about_data'] = ABOUT_US_DATA
        return context


# ============================================================
# 2. NOTICIAS
# ============================================================


def news_public_list_frontend(request):
    query = request.GET.get('q', '').strip()
    news_list = News.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-created_at')
    if query:
        news_list = news_list.filter(Q(title__icontains=query) | Q(summary__icontains=query))
    
    # Cambiamos 'news_list' por 'object_list' para que la tarjeta genérica lo lea
    context = {
        'object_list': news_list, 
        'page_title': 'Noticias', 
        'page_subtitle': 'Últimas noticias del Concejo',
        'detail_url_name': 'core:news_detail_frontend', 
        'detail_btn_label': 'Leer Noticia',
        'query': query
    }
    return render(request, 'core/generic_cards_grid.html', context)


def news_detail_frontend(request, pk):
    try:
        news_item = News.objects.get(pk=pk, is_active=True)
        related_news = News.objects.filter(is_active=True, category=news_item.category).exclude(pk=pk).order_by('-created_at')[:3] if news_item.category else News.objects.filter(is_active=True).exclude(pk=pk).order_by('-created_at')[:3]
    except News.DoesNotExist:
        fallback = next((item for item in NEWS_DATA if item['id'] == pk), None)
        if fallback:
            news_item = SimpleNamespace(pk=fallback['id'], id=fallback['id'], title=fallback['title'], name=fallback['title'], slug=None, summary=fallback['description'], description=fallback['description'], content=fallback['description'], image=SimpleNamespace(url=fallback['image']), category=SimpleNamespace(name=fallback['category']), created_at=fallback['date'], publication_date=fallback['date'], author='Concejo Municipal', attached_file=None, show_pdf_inline=False, social_media_url=None)
            related_news = []
        else: raise Http404("La noticia no existe.")

    return render(request, 'core/generic_detail.html', {'object': news_item, 'news_item': news_item, 'related_news': related_news, 'detail_url_name': 'core:news_detail_frontend', 'is_news_detail': True})


class NewsManageView(CanEditHomeMixin, ListView):
    model = News
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    
    def get_queryset(self):
        qs = News.objects.all().order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q) #  Buscador
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'page_title': 'Gestión de Noticias', 
            'header_icon': 'bi-newspaper', 
            'create_url': 'core:create_news_frontend', 
            'create_label': 'Nueva Noticia', 
            'detail_url_name': 'core:news_detail_frontend', 
            'update_url_name': 'core:update_news_frontend', 
            'delete_url_name': 'core:delete_news_frontend',
            'search_url': reverse_lazy('core:manage_news_frontend') #  Activamos el buscador
        })
        return ctx



class NewsCreateView(CanEditHomeMixin, CreateView):
    model = News
    form_class = NewsForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_news_frontend')
    extra_context = {'form_title': 'Registrar Nueva Noticia'}
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class NewsUpdateView(CanEditHomeMixin, UpdateView):
    model = News
    form_class = NewsForm 
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_news_frontend')
    extra_context = {'form_title': 'Editar Noticia'}

class NewsDeleteView(CanEditHomeMixin, DeleteView):
    model = News
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_news_frontend')
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Noticia eliminada.')
        return super().delete(request, *args, **kwargs)


# ============================================================
# 3. CRÓNICAS
# ============================================================

class ChronicleListView(ListView):
    model = Chronicle
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    extra_context = {'page_title': 'Crónicas', 'detail_url_name': 'core:chronicle_detail', 'detail_btn_label': 'Leer Crónica'}
    def get_queryset(self): return Chronicle.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-created_at')

class ChronicleDetailView(DetailView):
    model = Chronicle
    template_name = 'core/generic_detail.html'
    context_object_name = 'object'
  
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'sidebar_title': 'Otras Crónicas', 'recent_items': Chronicle.objects.filter(is_active=True).exclude(pk=self.object.pk)[:3], 'back_url': reverse_lazy('core:chronicle_public_list'), 'detail_url_name': 'core:chronicle_detail'})
        return ctx


class ChronicleManageView(CanEditHomeMixin, ListView):
    model = Chronicle
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    paginate_by = 15
    def get_queryset(self):
        qs = Chronicle.objects.all().order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión de Crónicas', 'header_icon': 'bi-book', 'create_url': 'core:create_chronicle', 'create_label': 'Nueva Crónica', 'detail_url_name': 'core:chronicle_detail', 'update_url_name': 'core:edit_chronicle', 'delete_url_name': 'core:delete_chronicle'})
        return ctx

class ChronicleCreateView(CanEditHomeMixin, CreateView):
    model = Chronicle
    form_class = ChronicleForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_chronicles')
    extra_context = {'form_title': 'Registrar Crónica'}
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ChronicleUpdateView(CanEditHomeMixin, UpdateView):
    model = Chronicle
    form_class = ChronicleForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_chronicles')
    extra_context = {'form_title': 'Editar Crónica'}

class ChronicleDeleteView(CanEditHomeMixin, DeleteView):
    model = Chronicle
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_chronicles')
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Crónica eliminada.')
        return super().delete(request, *args, **kwargs)


# ============================================================
# 4. CATEGORÍAS (CON TRY/EXCEPT)
# ============================================================

class CategoryManageView(CanEditHomeMixin, ListView):
    model = Category
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Category.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(name__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión de Categorías', 'header_icon': 'bi-tags', 'create_url': 'core:create_category_frontend', 'create_label': 'Nueva Categoría', 'update_url_name': 'core:update_category_frontend', 'delete_url_name': 'core:delete_category_frontend'})
        return ctx

class CategoryCreateView(CanEditHomeMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_categories_frontend')

class CategoryUpdateView(CanEditHomeMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_categories_frontend')

class CategoryDeleteView(CanEditHomeMixin, DeleteView):
    model = Category
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_categories_frontend')
    def delete(self, request, *args, **kwargs):
        try:

            # 1. Intentamos borrar primero
            response = super().delete(request, *args, **kwargs)
            # 2. Si no explotó, mostramos el éxito
            messages.success(request, 'Categoría eliminada.')
            return response
        except ProtectedError: 
            # 3. Si explotó por relación, mostramos el error amigable
            messages.error(request, "No puedes eliminar esta categoría porque tiene noticias asignadas.")
            return redirect(self.success_url)


# ============================================================
# 5. COMISIONES (CON TRY/EXCEPT)
# ============================================================

class CommissionsView(ListView):
    model = Commission
    template_name = 'core/commissions.html'
    context_object_name = 'commissions'
    def get_queryset(self): return Commission.objects.select_related('president', 'vice_president', 'vocal').order_by('number')

class CommissionAdminListView(CanEditHomeMixin, ListView):
    model = Commission
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Commission.objects.select_related('president', 'vice_president', 'vocal').order_by('number')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(name__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión de Comisiones', 'header_icon': 'bi-people', 'create_url': 'core:commission_create', 'update_url_name': 'core:commission_update', 'delete_url_name': 'core:commission_delete'})
        return ctx

class CommissionCreateView(CanEditHomeMixin, CreateView):
    model = Commission
    form_class = CommissionForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:commission_admin_list')

class CommissionUpdateView(CanEditHomeMixin, UpdateView):
    model = Commission
    form_class = CommissionForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:commission_admin_list')


class CommissionDeleteView(CanEditHomeMixin, DeleteView):
    model = Commission
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:commission_admin_list')

    def delete(self, request, *args, **kwargs):
        try:
            # 1. Intentamos borrar primero
            response = super().delete(request, *args, **kwargs)
            # 2. Si no explotó, mostramos el éxito
            messages.success(request, 'Comisión eliminada correctamente.')
            return response
        except ProtectedError:
            # 3. Si explotó por relación, mostramos el error amigable
            messages.error(request, "No puedes eliminar esta comisión porque tiene miembros asignados.")
            return redirect(self.success_url)


# ============================================================
# 6. CONCEJALES (CON TRY/EXCEPT)
# ============================================================

class CouncilorListView(ListView):
    model = Councilor
    template_name = 'core/councilors.html' 
    context_object_name = 'councilors'     

    def get_queryset(self):
        return Councilor.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        # Separación por jerarquía usando el campo author (Cargo)
        context['presidente'] = qs.filter(author='Presidente').first()
        context['vicepresidente'] = qs.filter(author='Vicepresidente').first()
        
        # Los concejales se ordenan alfabéticamente por su nombre
        context['concejales'] = qs.filter(author='Concejal').order_by('title') 
        
        # Síndico y Secretaria (usamos filter en lugar de first para permitir varios si los hay)
        context['sindico'] = qs.filter(author='Síndico Procurador')
        context['secretario'] = qs.filter(author='Secretario(a)')

        return context


class CouncilorDetailView(DetailView):
    model = Councilor
    template_name = 'core/generic_detail.html'
    context_object_name = 'object'
   
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'sidebar_title': 'Otros Concejales', 'recent_items': Councilor.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4], 'back_url': reverse_lazy('core:councilor_list'), 'detail_url_name': 'core:councilor_detail'})
        return ctx


class CouncilorManageView(CanEditHomeMixin, ListView):
    model = Councilor
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Councilor.objects.all().order_by('author')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'page_title': 'Gestión de Concejales', 
            'header_icon': 'bi-person-badge', 
            'create_url': 'core:councilor_create', 
            'update_url_name': 'core:councilor_update', 
            'delete_url_name': 'core:councilor_delete',
            'search_url': reverse_lazy('core:manage_councilors')
        })
        return ctx


class CouncilorCreateView(CanEditHomeMixin, CreateView):
    model = Councilor
    form_class = CouncilorForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:councilor_list')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class CouncilorUpdateView(CanEditHomeMixin, UpdateView):
    model = Councilor
    form_class = CouncilorForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:councilor_list')

class CouncilorDeleteView(CanEditHomeMixin, DeleteView):
    model = Councilor
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:councilor_list')
    def delete(self, request, *args, **kwargs):
        try:
            # 1. Intentamos borrar primero
            response = super().delete(request, *args, **kwargs)
             # 2. Si no explotó, mostramos el éxito
            messages.success(request, 'Concejal eliminado.')
            return response
        except ProtectedError:
            # 3. Si explotó por relación, mostramos el error amigable 
            messages.error(request, "No puedes eliminar este concejal porque pertenece a una comisión activa.")
            return redirect(self.success_url)



# ============================================================
# 7. LEGISLATURAS (CON TRY/EXCEPT Y TITLE VIRTUAL)
# ============================================================

class LegislatureListView(ListView):
    model = Legislature
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    extra_context = {'page_title': 'Legislaturas', 'page_subtitle': 'Historial de periodos legislativos'}
    def get_queryset(self): return Legislature.objects.prefetch_related('members').order_by('order')
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for leg in ctx['object_list']: leg.title = f"Legislatura {leg.roman_id} ({leg.years})" 
        return ctx

class LegislatureCreateView(CanEditHomeMixin, CreateView):
    model = Legislature
    form_class = LegislatureForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:legislature_list')


class LegislatureManageView(CanEditHomeMixin, ListView):
    model = Legislature
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Legislature.objects.all().order_by('-order')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(roman_id__icontains=q)
        return qs
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Inyectamos el título virtual para que la tabla no explote
        for leg in ctx['object_list']: 
            leg.title = f"Legislatura {leg.roman_id} ({leg.years})" 
            
        ctx.update({
            'page_title': 'Gestión de Legislaturas', 
            'header_icon': 'bi-bank', 
            'create_url': 'core:legislature_create', 
            'update_url_name': 'core:legislature_update', 
            'delete_url_name': 'core:legislature_delete',
            'search_url': reverse_lazy('core:manage_legislatures')
        })
        return ctx


class LegislatureUpdateView(CanEditHomeMixin, UpdateView):
    model = Legislature
    form_class = LegislatureForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:legislature_list')


class LegislatureDeleteView(CanEditHomeMixin, DeleteView):
    model = Legislature
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:legislature_list')

    def delete(self, request, *args, **kwargs):
        # Como los legisladores usan CASCADE, se borrarán junto con la legislatura.
        # Ya no es necesario el try/except ProtectedError.
        messages.success(request, 'Legislatura y sus legisladores asociados eliminados correctamente.')
        return super().delete(request, *args, **kwargs)


# ============================================================
# 8. ACTIVIDADES Y SUBTIPOS
# ============================================================

class AnnouncementListView(ListView):
    model = Announcement
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    extra_context = {'page_title': 'Licitaciones', 'detail_url_name': 'core:announcement_detail'}
    def get_queryset(self): return Announcement.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-start_date')

class AnnouncementDetailView(DetailView):
    model = Announcement
    template_name = 'core/generic_detail.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'sidebar_title': 'Otras Licitaciones', 'recent_items': Announcement.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4], 'back_url': reverse_lazy('core:announcement_list'), 'detail_url_name': 'core:announcement_detail'})
        return ctx

class AnnouncementManageView(CanEditHomeMixin, ListView):
    model = Announcement
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Announcement.objects.all().order_by('-start_date')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión de Licitaciones', 'header_icon': 'bi-megaphone', 'create_url': 'core:announcement_create', 'update_url_name': 'core:announcement_update', 'delete_url_name': 'core:announcement_delete'})
        return ctx

class AnnouncementCreateView(CanEditHomeMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_announcements')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class AnnouncementUpdateView(CanEditHomeMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_announcements')

class AnnouncementDeleteView(CanEditHomeMixin, DeleteView):
    model = Announcement
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_announcements')
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Licitación eliminada.')
        return super().delete(request, *args, **kwargs)


# --- CONSULTAS ---
class ConsultationListView(ListView):
    model = Consultation
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    extra_context = {'page_title': 'Consultas Públicas', 'detail_url_name': 'core:consultation_detail'}
    def get_queryset(self): return Consultation.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-start_date')

class ConsultationDetailView(DetailView):
    model = Consultation
    template_name = 'core/generic_detail.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'sidebar_title': 'Otras Consultas', 'recent_items': Consultation.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4], 'back_url': reverse_lazy('core:consultation_list'), 'detail_url_name': 'core:consultation_detail'})
        return ctx

class ConsultationManageView(CanEditHomeMixin, ListView):
    model = Consultation
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Consultation.objects.all().order_by('-start_date')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión de Consultas', 'header_icon': 'bi-people', 'create_url': 'core:consultation_create', 'update_url_name': 'core:consultation_update', 'delete_url_name': 'core:consultation_delete'})
        return ctx

class ConsultationCreateView(CanEditHomeMixin, CreateView):
    model = Consultation
    form_class = ConsultationForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_consultations')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ConsultationUpdateView(CanEditHomeMixin, UpdateView):
    model = Consultation
    form_class = ConsultationForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_consultations')

class ConsultationDeleteView(CanEditHomeMixin, DeleteView):
    model = Consultation
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_consultations')
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Consulta eliminada.')
        return super().delete(request, *args, **kwargs)


# --- EVENTOS ---
class EventListView(ListView):
    model = Event
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    extra_context = {'page_title': 'Eventos', 'detail_url_name': 'core:event_detail'}
    def get_queryset(self): return Event.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-start_date')

class EventDetailView(DetailView):
    model = Event
    template_name = 'core/generic_detail.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'sidebar_title': 'Próximos Eventos', 'recent_items': Event.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4], 'back_url': reverse_lazy('core:event_list'), 'detail_url_name': 'core:event_detail'})
        return ctx

class EventManageView(CanEditHomeMixin, ListView):
    model = Event
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Event.objects.all().order_by('-start_date')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión de Eventos', 'header_icon': 'bi-calendar-event', 'create_url': 'core:event_create', 'update_url_name': 'core:event_update', 'delete_url_name': 'core:event_delete'})
        return ctx

class EventCreateView(CanEditHomeMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_events')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class EventUpdateView(CanEditHomeMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_events')

class EventDeleteView(CanEditHomeMixin, DeleteView):
    model = Event
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_events')
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Evento eliminado.')
        return super().delete(request, *args, **kwargs)


# --- DESCARGABLES ---

class DownloadableListView(ListView):
    model = Downloadable
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    
    def get_queryset(self):
        qs = Downloadable.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs
        
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'page_title': 'Descargables', 
            'detail_btn_label': 'Descargar PDF',
            'search_url': reverse_lazy('core:downloadable_list') #  Buscador para el público
        })
        return ctx


class DownloadableManageView(CanEditHomeMixin, ListView):
    model = Downloadable
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Downloadable.objects.all().order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión de Descargables', 'header_icon': 'bi-file-earmark-arrow-down', 'create_url': 'core:downloadable_create', 'update_url_name': 'core:downloadable_update', 'delete_url_name': 'core:delete_downloadable'})
        return ctx


class DownloadableCreateView(CanEditHomeMixin, CreateView):
    model = Downloadable
    form_class = DownloadableForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_downloadables')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class DownloadableUpdateView(CanEditHomeMixin, UpdateView):
    model = Downloadable
    form_class = DownloadableForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_downloadables')

class DownloadableDeleteView(CanEditHomeMixin, DeleteView):
    model = Downloadable
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_downloadables')
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Descargable eliminado.')
        return super().delete(request, *args, **kwargs)


# ============================================================
# 9. ACTIVIDADES (SOLO LECTURA) Y SOBRE NOSOTROS
# ============================================================

class ActivityListView(ListView):
    model = Activity
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    extra_context = {'page_title': 'Actividades', 'detail_url_name': 'core:activity_detail'}
    def get_queryset(self): return Activity.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-created_at')

class ActivityDetailView(DetailView):
    model = Activity
    template_name = 'core/generic_detail.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'sidebar_title': 'Otras Actividades', 'recent_items': Activity.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4], 'back_url': reverse_lazy('core:activity_list'), 'detail_url_name': 'core:activity_detail'})
        return ctx

class ActivityManageView(CanEditHomeMixin, ListView):
    model = Activity
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        qs = Activity.objects.all().order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q: qs = qs.filter(title__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'page_title': 'Gestión de Actividades', 
            'header_icon': 'bi-activity', 
            'detail_url_name': 'core:activity_detail',
            'search_url': reverse_lazy('core:manage_activities') # Buscador
        })
        return ctx


class AboutUsManageView(CanEditHomeMixin, ListView):
    model = AboutUs
    template_name = 'core/generic_admin_list.html'
    context_object_name = 'object_list'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({'page_title': 'Gestión Institucional', 'header_icon': 'bi-info-circle', 'update_url_name': 'core:about_us_update'})
        return ctx

class AboutUsUpdateView(CanEditHomeMixin, UpdateView):
    model = AboutUs
    form_class = AboutUsForm
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('core:manage_about_us')