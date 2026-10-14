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

import logging
from types import SimpleNamespace

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, ProtectedError
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404

# Modelos externos
from documents.models import Document, Gazette

# Modelos locales (Arquitectura BaseContent)
from .models import (
    BaseContent, News, Chronicle, Councilor, AboutUs,
    Activity, Announcement, Consultation, Event, Downloadable,
    Category, Commission, Legislature, Legislator
)
from .forms import (
    NewsForm, 
    CategoryForm, 
    ChronicleForm, 
    CommissionForm, 
    AboutUsForm, 
    ActivityForm,
    AnnouncementForm,
    ConsultationForm,
    EventForm,
    DownloadableForm, 
    LegislatureForm,
)

User = get_user_model()
logger = logging.getLogger(__name__)

"""
1-ESTE VIEW DEBE SER ADAPTADO A LA NUEVA ESTRUCTURA DE MODELS AUN NO ESTA INCORPORADA (model-core)
SE DEBE ACTUALIZAR PRIMERO LOS MODELOS

"""


# ============================================================
# DATOS ESTÁTICOS DE RESPALDO (FALLBACKS)
# ============================================================

NEWS_DATA = [
    {
        'id': 1,
        'title': 'Concejo Municipal fortalece labores de rescate de los «Ángeles de la Autopista»',
        'description': 'En el marco de la Sesión Ordinaria N° 55, el Concejo Municipal concretó la entrega formal de una antena Starlink al cuerpo paramédico.',
        'image': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800',
        'date': '20 de agosto de 2026',
        'category': 'Social',
    },
    {
        'id': 2,
        'title': 'Nueva ordenanza para la protección del medio ambiente',
        'description': 'El Concejo Municipal aprobó la ordenanza que regula el uso de plásticos de un solo uso en el municipio Junín.',
        'image': 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800',
        'date': '18 de agosto de 2026',
        'category': 'Cultura',
    },
    {
        'id': 3,
        'title': 'Jornada de atención al ciudadano en Rubio',
        'description': 'Jornada integral de atención ciudadana realizada en la plaza Bolívar de Rubio.',
        'image': 'https://images.unsplash.com/photo-1573164713988-8665fc963095?w=800',
        'date': '15 de agosto de 2026',
        'category': 'Salud',
    },
]

SYNDICATE_DATA = [
    {
        'name': 'Abogado por designar',
        'position': 'Síndico Procurador Municipal',
        'image': 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=400',
    },
    {
        'name': 'Daymar C.',
        'position': 'Secretaria Municipal del Concejo',
        'image': 'https://images.unsplash.com/photo-1580894732444-8ecded7900cd?w=400',
    },
]

ABOUT_US_DATA = {
    'who_we_are': (
        'El Concejo Municipal del Municipio Junín es un órgano colegiado, legislativo y deliberante, '
        'integrado por siete (7) concejales principales elegidos mediante voto popular.'
    ),
    'mission': (
        'Ejercer la función legislativa municipal mediante la creación, discusión y aprobación de ordenanzas locales.'
    ),
    'vision': (
        'Ser una institución legislativa de vanguardia, transparente, eficiente y cercana a los ciudadanos de Junín.'
    ),
    'image_main': 'core/img/quienes_somos_junin.jpg'
}


# ============================================================
# 1. PANEL DE CONTROL (DASHBOARD ADMINISTRATIVO)
# ============================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """Panel de control con métricas generales aisladas contra fallas."""
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            context['total_documents'] = Document.objects.count()
            context['total_gazettes'] = Gazette.objects.count()
            context['total_users'] = User.objects.count()
        except Exception as e:
            logger.error(f"Error cargando contadores globales en DashboardView: {e}")
            context['total_documents'] = 0
            context['total_gazettes'] = 0
            context['total_users'] = 0

        # Cálculo seguro de elementos en papelera
        try:
            try:
                from common.views import TRASH_MODELS
            except ImportError:
                from apps.common.views import TRASH_MODELS

            trash_count = 0
            for model in TRASH_MODELS:
                if hasattr(model, 'all_objects') and hasattr(model, 'deleted_at'):
                    trash_count += model.all_objects.filter(deleted_at__isnull=False).count()
                elif hasattr(model, 'objects') and hasattr(model, 'deleted_at'):
                    trash_count += model.objects.filter(deleted_at__isnull=False).count()

            context['total_trash'] = trash_count
        except Exception as e:
            logger.error(f"Error calculando papelera en DashboardView: {e}")
            context['total_trash'] = 0

        try:
            context['recent_documents'] = Document.objects.select_related(
                'document_type', 'gazette'
            ).order_by('-created_at')[:5]
        except Exception as e:
            logger.error(f"Error cargando documentos recientes: {e}")
            context['recent_documents'] = []

        try:
            context['approved_count'] = Document.objects.filter(is_approved=True, is_annulled=False).count()
            context['pending_count'] = Document.objects.filter(is_approved=False, is_annulled=False).count()
            context['annulled_count'] = Document.objects.filter(is_annulled=True).count()
        except Exception as e:
            logger.error(f"Error calculando métricas de estado de documentos: {e}")
            context['approved_count'] = 0
            context['pending_count'] = 0
            context['annulled_count'] = 0

        return context


# ============================================================
# 2. PORTAL PÚBLICO GENERAL (HOME & INSTITUCIONAL)
# ============================================================

class HomeView(TemplateView):

    """Portada web con resiliencia y datos estáticos de respaldo."""

    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        try:
            context['documentos_destacados'] = Document.objects.select_related(
                'gazette', 'document_type'
            ).order_by('-emission_date')[:2]
            context['ultimas_gacetas'] = Gazette.objects.all()[:3]
        except Exception as e:
            logger.error(f"Error cargando documentos en HomeView: {e}")
            context['documentos_destacados'] = []
            context['ultimas_gacetas'] = []


        # 1. Noticias para el carrusel principal

        try:
            carousel = News.objects.filter(
                is_active=True, 
                status=BaseContent.Status.PUBLISHED
            ).order_by('-publication_date')[:3]
            context['carousel_news'] = carousel if carousel.exists() else NEWS_DATA
        except Exception as e:
            logger.error(f"Error cargando noticias de carrusel: {e}")
            context['carousel_news'] = NEWS_DATA


        # 2. Crónicas municipales recientes
        try:
            context['carousel_activities'] = Activity.objects.filter(
                is_active=True, 
                status=BaseContent.Status.PUBLISHED, 
                is_featured=True
            ).order_by('-publication_date')[:3]
        except Exception as e:
            logger.error(f"Error cargando actividades en HomeView: {e}")
            context['carousel_activities'] = []

        try:
            context['chronicles'] = Chronicle.objects.filter(
                is_active=True, 
                status=BaseContent.Status.PUBLISHED
            ).order_by('-publication_date')[:3]
        except Exception as e:
            logger.error(f"Error cargando crónicas en HomeView: {e}")
            context['chronicles'] = []


        # 3. Listado secundario de noticias
        try:
            context['consultations'] = Consultation.objects.filter(
                is_active=True, 
                status=BaseContent.Status.PUBLISHED
            ).order_by('-start_date')[:3]
        except Exception as e:
            logger.error(f"Error cargando consultas públicas: {e}")
            context['consultations'] = []

        try:
            news_qs = News.objects.filter(
                is_active=True, 
                status=BaseContent.Status.PUBLISHED
            ).order_by('-publication_date')
            context['news_list'] = news_qs[:3] if news_qs.exists() else NEWS_DATA
        except Exception as e:
            logger.error(f"Error cargando noticias secundarias: {e}")
            context['news_list'] = NEWS_DATA


        # 4. Listado de Concejales para la portada
        try:
            context['councilors'] = Councilor.objects.filter(
                is_active=True, 
                status=BaseContent.Status.PUBLISHED
            ).order_by('order')
        except Exception as e:
            logger.error(f"Error cargando concejales en HomeView: {e}")
            context['councilors'] = []

        return context



class AboutUsView(TemplateView):
    """Página institucional con respaldo local."""
    template_name = 'core/about_us.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            about_items = AboutUs.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED)
            who = about_items.filter(slug='quienes-somos').first()
            mission = about_items.filter(slug='mision').first()
            vision = about_items.filter(slug='vision').first()

            context['about_data'] = {
                'who_we_are': who.content if who else ABOUT_US_DATA['who_we_are'],
                'mission': mission.content if mission else ABOUT_US_DATA['mission'],
                'vision': vision.content if vision else ABOUT_US_DATA['vision'],
                'image_main': ABOUT_US_DATA['image_main']
            }
        except Exception as e:
            logger.error(f"Error cargando información institucional: {e}")
            context['about_data'] = ABOUT_US_DATA

        try:
            context['legislatures'] = Legislature.objects.prefetch_related('members').all()
        except Exception as e:
            logger.error(f"Error cargando legislaturas en AboutUsView: {e}")
            context['legislatures'] = []

        return context



# ============================================================
# 2. PANEL DE CONTROL (DASHBOARD ADMINISTRATIVO)
# ============================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """Panel de control con métricas generales del sistema."""
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # KPI Cards
        context['total_documents'] = Document.objects.count()
        context['total_gazettes'] = Gazette.objects.count()
        context['total_users'] = User.objects.count()

        # Papelera — try/except defensivo: si falla un contador, se
        # muestra 0 en vez de tumbar todo el dashboard.
        try:
            from common.views import TRASH_MODELS
            trash_count = 0
            for model in TRASH_MODELS:
                trash_count += model.all_objects.filter(deleted_at__isnull=False).count()
            context['total_trash'] = trash_count
        except Exception:
            context['total_trash'] = 0

        # Documentos recientes
        context['recent_documents'] = Document.objects.select_related(
            'document_type', 'gazette'
        ).order_by('-created_at')[:5]

        # Datos para el gráfico (3 categorías)
        context['approved_count'] = Document.objects.filter(is_approved=True, is_annulled=False).count()
        context['pending_count'] = Document.objects.filter(is_approved=False, is_annulled=False).count()
        context['annulled_count'] = Document.objects.filter(is_annulled=True).count()

        return context


# ============================================================
# 3. MÓDULO DE NOTICIAS (FRONTEND Y GESTIÓN)
# ============================================================

def news_public_list_frontend(request):
    """Listado público de noticias activas con filtros por texto, fecha y categoría."""
    query = request.GET.get('q', '').strip()
    date_query = request.GET.get('date', '').strip()
    category_slug = request.GET.get('category', '').strip()

    news_list = News.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-publication_date')
    categories = Category.objects.all()

    if query:
        news_list = news_list.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query)
        )

    if date_query:
        try:
            news_list = news_list.filter(publication_date__date=date_query)
        except (ValidationError, ValueError):
            date_query = ''

    if category_slug:
        news_list = news_list.filter(category__slug=category_slug)

    context = {
        'news_list': news_list,
        'categories': categories,
        'query': query,
        'date_query': date_query,
        'selected_category': category_slug,
    }
    return render(request, 'core/news_public_list.html', context)


def news_detail_frontend(request, pk):
    """Detalle individual de noticia con fallback sintético."""
    try:
        news_item = News.objects.get(pk=pk, is_active=True)
        if news_item.category:
            related_news = News.objects.filter(
                is_active=True, category=news_item.category
            ).exclude(pk=pk).order_by('-publication_date')[:3]
        else:
            related_news = News.objects.filter(is_active=True).exclude(pk=pk).order_by('-publication_date')[:3]

    except News.DoesNotExist:
        fallback = next((item for item in NEWS_DATA if item['id'] == pk), None)
        if fallback:
            news_item = SimpleNamespace(
                id=fallback['id'],
                title=fallback['title'],
                summary=fallback['description'],
                content=fallback['description'],
                image=SimpleNamespace(url=fallback['image']) if fallback.get('image') else None,
                category=SimpleNamespace(name=fallback['category']) if fallback.get('category') else None,
                publication_date=fallback['date'],
                pdf_file=None,
                show_pdf_inline=False,
                social_media_url=None,
            )
            related_news = []
        else:
            raise Http404("La noticia solicitada no existe.")

    context = {
        'news_item': news_item,
        'related_news': related_news,
    }
    return render(request, 'core/news_detail.html', context)


class NewsManageView(LoginRequiredMixin, ListView):
    """Listado de noticias para administración."""
    model = News
    template_name = 'core/manage_news.html'
    context_object_name = 'news_list'
    paginate_by = 20

    def get_queryset(self):
        # El manager proxy automatiza el filtrado por ContentType.NEWS
        return News.objects.all().order_by('-publication_date')


class NewsCreateView(LoginRequiredMixin, CreateView):
    """Creación administrativa de noticia."""
    model = News
    form_class = NewsForm
    template_name = 'core/save_news.html'
    success_url = reverse_lazy('core:manage_news_frontend')

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.NEWS
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, 'Noticia creada exitosamente.')
        return super().form_valid(form)


class NewsUpdateView(LoginRequiredMixin, UpdateView):
    """Edición administrativa de noticia."""
    model = News
    form_class = NewsForm
    template_name = 'core/save_news.html'
    success_url = reverse_lazy('core:manage_news_frontend')

    def form_valid(self, form):
        messages.success(self.request, 'Noticia actualizada exitosamente.')
        return super().form_valid(form)


class NewsDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación administrativa de noticia."""
    model = News
    template_name = 'core/delete_news.html'
    success_url = reverse_lazy('core:manage_news_frontend')


# ============================================================
# 4. MÓDULO DE CRÓNICAS MUNICIPALES (FRONTEND Y GESTIÓN)
# ============================================================

def chronicle_public_list(request):
    """Listado público de crónicas históricas activas."""
    chronicles = Chronicle.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'core/chronicles_public_list.html', {'chronicles': chronicles})


def chronicle_detail(request, slug):
    """Lectura detallada de una crónica específica."""
    chronicle = get_object_or_404(Chronicle, slug=slug, is_active=True)
    recent_chronicles = Chronicle.objects.filter(is_active=True).exclude(pk=chronicle.pk).order_by('-created_at')[:3]
    return render(request, 'core/chronicles_detail.html', {
        'chronicle': chronicle,
        'recent_chronicles': recent_chronicles
    })


@login_required
def manage_chronicles(request):
    """Panel administrativo para listar crónicas."""
    chronicles = Chronicle.objects.all().order_by('-created_at')
    return render(request, 'core/manage_chronicles.html', {'chronicles': chronicles})


@login_required
def save_chronicle(request, pk=None):
    """Vista unificada para Crear o Editar una crónica."""
    chronicle = get_object_or_404(Chronicle, pk=pk) if pk else None

    if request.method == 'POST':
        form = ChronicleForm(request.POST, request.FILES, instance=chronicle)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Crónica guardada exitosamente!")
            return redirect('core:manage_chronicles')
    else:
        form = ChronicleForm(instance=chronicle)

    return render(request, 'core/save_chronicles.html', {
        'form': form,
        'editing': bool(pk)
    })


@login_required
def delete_chronicle(request, pk):
    """Acción para eliminar una crónica."""
    chronicle = get_object_or_404(Chronicle, pk=pk)
    if request.method == 'POST':
        chronicle.delete()
        messages.success(request, "Crónica eliminada correctamente.")
        return redirect('core:manage_chronicles')
    return render(request, 'core/delete_chronicle.html', {'chronicle': chronicle})


# ============================================================
# 5. MÓDULO DE CATEGORÍAS (GESTIÓN INTERNA)
# ============================================================

class ChronicleListView(ListView):
    """Listado público de crónicas."""
    model = Chronicle
    template_name = 'core/chronicles_public_list.html'
    context_object_name = 'chronicles'

    def get_queryset(self):
        return Chronicle.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-publication_date')


class ChronicleDetailView(DetailView):
    """Detalle de una crónica por slug."""
    model = Chronicle
    template_name = 'core/chronicle_detail.html'
    context_object_name = 'chronicle'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_chronicles'] = Chronicle.objects.filter(
            is_active=True
        ).exclude(pk=self.object.pk).order_by('-publication_date')[:3]
        return context


class ChronicleManageView(LoginRequiredMixin, ListView):
    """Gestión administrativa de crónicas."""
    model = Chronicle
    template_name = 'core/manage_chronicles.html'
    context_object_name = 'chronicles'

    def get_queryset(self):
        return Chronicle.objects.all().order_by('-publication_date')


class ChronicleCreateView(LoginRequiredMixin, CreateView):
    """Creación de crónica."""
    model = Chronicle
    form_class = ChronicleForm
    template_name = 'core/save_chronicles.html'
    success_url = reverse_lazy('core:manage_chronicles')

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.CHRONICLE
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, "¡Crónica guardada exitosamente!")
        return super().form_valid(form)


class ChronicleUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de crónica."""
    model = Chronicle
    form_class = ChronicleForm
    template_name = 'core/save_chronicles.html'
    success_url = reverse_lazy('core:manage_chronicles')


class ChronicleDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de crónica."""
    model = Chronicle
    template_name = 'core/delete_chronicle.html'
    success_url = reverse_lazy('core:manage_chronicles')


# ============================================================
# 5. MÓDULO DE CATEGORÍAS (GESTIÓN)
# ============================================================

class CategoryManageView(LoginRequiredMixin, ListView):
    """Gestión de categorías."""
    model = Category
    template_name = 'core/manage_categories.html'
    context_object_name = 'categories'


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Creación de categoría."""
    model = Category
    form_class = CategoryForm
    template_name = 'core/save_category.html'
    success_url = reverse_lazy('core:manage_categories_frontend')


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de categoría."""
    model = Category
    form_class = CategoryForm
    template_name = 'core/save_category.html'
    success_url = reverse_lazy('core:manage_categories_frontend')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de categoría."""
    model = Category
    template_name = 'core/delete_category.html'
    success_url = reverse_lazy('core:manage_categories_frontend')


# ============================================================
# 6. MÓDULO DE COMISIONES PERMANENTES
# ============================================================

class CommissionsView(ListView):
    """Vista pública de comisiones optimizada para prefetch."""

    model = Commission
    template_name = 'core/commissions.html'
    context_object_name = 'commissions'

    def get_queryset(self):

        return Commission.objects.prefetch_related('members__councilor').order_by('number')


class CommissionAdminListView(LoginRequiredMixin, ListView):
    """Gestión de comisiones."""
    model = Commission
    template_name = 'core/commission_admin_list.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        return Commission.objects.prefetch_related('members__councilor').order_by('number')


class CommissionCreateView(LoginRequiredMixin, CreateView):
    """Crear comisión."""
    model = Commission
    form_class = CommissionForm
    template_name = 'core/commission_form.html'
    success_url = reverse_lazy('core:commission_admin_list')


class CommissionUpdateView(LoginRequiredMixin, UpdateView):
    """Editar comisión."""
    model = Commission
    form_class = CommissionForm
    template_name = 'core/commission_form.html'
    success_url = reverse_lazy('core:commission_admin_list')


class CommissionDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar comisión capturando restricciones de clave foránea."""
    model = Commission
    template_name = 'core/commission_confirm_delete.html'
    success_url = reverse_lazy('core:commission_admin_list')


    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Comisión eliminada correctamente.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar esta comisión porque tiene miembros con asignación activa. "
                "Reasigne o elimine los miembros primero."
            )
            return redirect(self.success_url)


# ============================================================
# 7. MÓDULO DE CONCEJALES Y DIRECTIVA
# ============================================================

class CouncilorListView(ListView):
    """Listado público de concejales y directiva."""
    model = Councilor
    template_name = 'core/councilors_public_list.html'
    context_object_name = 'councilors'

    def get_queryset(self):
        return Councilor.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            syndicate_qs = Councilor.objects.filter(
                is_active=True, 
                status=BaseContent.Status.PUBLISHED,
                author__in=['Síndico Procurador Municipal', 'Secretaria Municipal del Concejo']
            ).order_by('order')
            context['syndicate'] = syndicate_qs if syndicate_qs.exists() else SYNDICATE_DATA
        except Exception:
            context['syndicate'] = SYNDICATE_DATA
        return context


class CouncilorDetailView(DetailView):
    """Perfil público individual de concejal."""
    model = Councilor
    template_name = 'core/councilor_detail.html'
    context_object_name = 'councilor'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


class CouncilorCreateView(LoginRequiredMixin, CreateView):
    """Crear concejal."""
    model = Councilor
    template_name = 'core/councilor_form.html'
    fields = ['title', 'author', 'summary', 'content', 'image', 'link', 'order', 'is_active', 'status']
    success_url = reverse_lazy('core:councilor_list')

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.COUNCILOR
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        return super().form_valid(form)


class CouncilorUpdateView(LoginRequiredMixin, UpdateView):
    """Editar concejal."""
    model = Councilor
    template_name = 'core/councilor_form.html'
    fields = ['title', 'author', 'summary', 'content', 'image', 'link', 'order', 'is_active', 'status']
    success_url = reverse_lazy('core:councilor_list')


class CouncilorDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar concejal capturando restricciones de clave foránea."""
    model = Councilor
    template_name = 'core/councilor_confirm_delete.html'
    success_url = reverse_lazy('core:councilor_list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Concejal eliminado correctamente.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar este concejal porque pertenece a una comisión o legislatura activa."
            )
            return redirect(self.success_url)


# ============================================================
# 8. MÓDULO DE LEGISLATURAS HISTÓRICAS
# ============================================================

class LegislatureListView(ListView):
    """Listado público de legislaturas."""
    model = Legislature
    template_name = 'core/legislatures_list.html'
    context_object_name = 'legislatures'

    def get_queryset(self):
        return Legislature.objects.prefetch_related('members').order_by('order')


class LegislatureCreateView(LoginRequiredMixin, CreateView):
    """Crear legislatura."""
    model = Legislature
    template_name = 'core/legislature_form.html'

    fields = ['roman_id', 'years', 'mayor', 'order']
    success_url = reverse_lazy('core:legislature_list')

    
    def form_valid(self, form):
        form.instance.content_type = HomeContent.ContentTypes.LEGISLATURE
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        return super().form_valid(form)



class LegislatureUpdateView(LoginRequiredMixin, UpdateView):
    """Editar legislatura."""
    model = Legislature
    template_name = 'core/legislature_form.html'

    fields = ['roman_id', 'years', 'mayor', 'order']
    success_url = reverse_lazy('core:legislature_list')



class LegislatureDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar legislatura capturando restricciones de clave foránea."""
    model = Legislature
    template_name = 'core/legislature_confirm_delete.html'

    success_url = reverse_lazy('core:legislature_list')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Legislatura eliminada correctamente.")
            return response
        except ProtectedError:
            messages.error(
                self.request,
                "No se puede eliminar esta legislatura porque posee legisladores vinculados."
            )
            return redirect(self.success_url)

# ============================================================
# 9. ACTIVIDADES, CONSULTAS, EVENTOS Y DESCARGABLES (GESTIÓN Y VISTAS PÚBLICAS)
# ============================================================

# --- LICITACIONES Y ANUNCIOS ---

class AnnouncementListView(ListView):
    """Listado público de Licitaciones y Anuncios."""
    model = Announcement
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    paginate_by = 9
    extra_context = {
        'page_title': 'Licitaciones y Anuncios',
        'page_subtitle': 'Convocatorias públicas y licitaciones del Municipio Junín',
        'detail_url_name': 'core:announcement_detail',
        'detail_btn_label': 'Ver Licitación',
    }

    def get_queryset(self):
        return Announcement.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-start_date')


class AnnouncementDetailView(DetailView):
    """Detalle público de una Licitación/Anuncio."""
    model = Announcement
    template_name = 'core/generic_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_title'] = 'Otras Licitaciones'
        context['recent_items'] = Announcement.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4]
        context['back_url'] = reverse_lazy('core:announcement_list')
        context['back_label'] = 'Volver a Licitaciones'
        return context


class AnnouncementManageView(LoginRequiredMixin, ListView):
    """Gestión de Licitaciones."""
    model = Announcement
    template_name = 'core/generic_admin_list.html'
    paginate_by = 15
    extra_context = {
        'page_title': 'Gestión de Licitaciones y Anuncios',
        'page_subtitle': 'Administración de procesos licitatorios y convocatorias oficiales',
        'header_icon': 'bi-megaphone',
        'create_url': 'core:announcement_create',
        'create_label': 'Nueva Licitación',
        'detail_url_name': 'core:announcement_detail',
        'update_url_name': 'core:announcement_update',
        'delete_url_name': 'core:announcement_delete',
    }

    def get_queryset(self):
        return Announcement.objects.all().order_by('-start_date')


class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    """Creación de Licitación."""
    model = Announcement
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'pdf_file', 'start_date', 'end_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_announcements')
    extra_context = {
        'form_title': 'Registrar Nueva Licitación',
        'form_subtitle': 'Publica las bases y condiciones para ofertas públicas',
        'form_icon': 'bi-megaphone-fill',
        'submit_label': 'Publicar Licitación',
        'cancel_url': reverse_lazy('core:manage_announcements'),
    }

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.ANNOUNCEMENT
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, "Anuncio o licitación creada correctamente.")
        return super().form_valid(form)


class AnnouncementUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de Licitación."""
    model = Announcement
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'pdf_file', 'start_date', 'end_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_announcements')
    extra_context = {
        'form_title': 'Editar Licitación',
        'form_subtitle': 'Modifica la información o extiende la fecha límite del anuncio',
        'form_icon': 'bi-pencil-square',
        'submit_label': 'Guardar Cambios',
        'cancel_url': reverse_lazy('core:manage_announcements'),
    }

    def form_valid(self, form):
        messages.success(self.request, "Anuncio o licitación actualizada.")
        return super().form_valid(form)


class AnnouncementDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de Licitación."""
    model = Announcement
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_announcements')
    extra_context = {
        'cancel_url': reverse_lazy('core:manage_announcements'),
    }


# --- CONSULTAS PÚBLICAS ---

class ConsultationListView(ListView):
    """Listado público de Consultas Ciudadanas."""
    model = Consultation
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    paginate_by = 9
    extra_context = {
        'page_title': 'Consultas Públicas',
        'page_subtitle': 'Participa en los proyectos normativos y ordenanzas en discusión',
        'detail_url_name': 'core:consultation_detail',
        'detail_btn_label': 'Participar / Ver más',
    }

    def get_queryset(self):
        return Consultation.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-start_date')


class ConsultationDetailView(DetailView):
    """Detalle público de una Consulta Ciudadana."""
    model = Consultation
    template_name = 'core/generic_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_title'] = 'Otras Consultas'
        context['recent_items'] = Consultation.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4]
        context['back_url'] = reverse_lazy('core:consultation_list')
        context['back_label'] = 'Volver a Consultas'
        return context


class ConsultationManageView(LoginRequiredMixin, ListView):
    """Gestión de Consultas Públicas."""
    model = Consultation
    template_name = 'core/generic_admin_list.html'
    paginate_by = 15
    extra_context = {
        'page_title': 'Gestión de Consultas Públicas',
        'page_subtitle': 'Administra las consultas abiertas para la participación vecinal',
        'header_icon': 'bi-people',
        'create_url': 'core:consultation_create',
        'create_label': 'Nueva Consulta',
        'detail_url_name': 'core:consultation_detail',
        'update_url_name': 'core:consultation_update',
        'delete_url_name': 'core:consultation_delete',
    }

    def get_queryset(self):
        return Consultation.objects.all().order_by('-start_date')


class ConsultationCreateView(LoginRequiredMixin, CreateView):
    """Creación de Consulta Pública."""
    model = Consultation
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'pdf_file', 'start_date', 'end_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_consultations')
    extra_context = {
        'form_title': 'Registrar Consulta Pública',
        'form_subtitle': 'Abre un nuevo proceso de consulta e intercambio ciudadano',
        'form_icon': 'bi-chat-left-quote',
        'submit_label': 'Publicar Consulta',
        'cancel_url': reverse_lazy('core:manage_consultations'),
    }

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.CONSULTATION
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, "Consulta pública registrada.")
        return super().form_valid(form)


class ConsultationUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de Consulta Pública."""
    model = Consultation
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'pdf_file', 'start_date', 'end_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_consultations')
    extra_context = {
        'form_title': 'Editar Consulta Pública',
        'form_subtitle': 'Modifica la descripción o fechas del proceso participativo',
        'form_icon': 'bi-pencil-square',
        'submit_label': 'Guardar Cambios',
        'cancel_url': reverse_lazy('core:manage_consultations'),
    }


class ConsultationDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de Consulta Pública."""
    model = Consultation
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_consultations')
    extra_context = {
        'cancel_url': reverse_lazy('core:manage_consultations'),
    }


# --- EVENTOS INSTITUCIONALES ---

class EventListView(ListView):
    """Listado público de Eventos del Concejo."""
    model = Event
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    paginate_by = 9
    extra_context = {
        'page_title': 'Agenda de Eventos',
        'page_subtitle': 'Sesiones solemnes, cabildos abiertos y actos de la cámara',
        'detail_url_name': 'core:event_detail',
        'detail_btn_label': 'Ver Evento',
    }

    def get_queryset(self):
        return Event.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-start_date')


class EventDetailView(DetailView):
    """Detalle público de un Evento."""
    model = Event
    template_name = 'core/generic_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_title'] = 'Próximos Eventos'
        context['recent_items'] = Event.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4]
        context['back_url'] = reverse_lazy('core:event_list')
        context['back_label'] = 'Volver a Eventos'
        return context


class EventManageView(LoginRequiredMixin, ListView):
    """Gestión de Eventos."""
    model = Event
    template_name = 'core/generic_admin_list.html'
    paginate_by = 15
    extra_context = {
        'page_title': 'Gestión de Eventos Institucionales',
        'page_subtitle': 'Administración de la agenda legislativa y actos públicos',
        'header_icon': 'bi-calendar-event',
        'create_url': 'core:event_create',
        'create_label': 'Nuevo Evento',
        'detail_url_name': 'core:event_detail',
        'update_url_name': 'core:event_update',
        'delete_url_name': 'core:event_delete',
    }

    def get_queryset(self):
        return Event.objects.all().order_by('-start_date')


class EventCreateView(LoginRequiredMixin, CreateView):
    """Creación de Evento."""
    model = Event
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'image', 'start_date', 'end_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_events')
    extra_context = {
        'form_title': 'Agendar Nuevo Evento',
        'form_subtitle': 'Añade una actividad o sesión a la agenda municipal',
        'form_icon': 'bi-calendar-plus',
        'submit_label': 'Agendar Evento',
        'cancel_url': reverse_lazy('core:manage_events'),
    }

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.EVENT
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, "Evento registrado con éxito.")
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de Evento."""
    model = Event
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'image', 'start_date', 'end_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_events')
    extra_context = {
        'form_title': 'Editar Evento',
        'form_subtitle': 'Actualiza la fecha, hora o descripción del evento',
        'form_icon': 'bi-pencil-square',
        'submit_label': 'Guardar Cambios',
        'cancel_url': reverse_lazy('core:manage_events'),
    }


class EventDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de Evento."""
    model = Event
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_events')
    extra_context = {
        'cancel_url': reverse_lazy('core:manage_events'),
    }


# --- DOCUMENTOS DESCARGABLES ---

class DownloadableListView(ListView):
    """Listado público de Documentos Descargables."""
    model = Downloadable
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    paginate_by = 12
    extra_context = {
        'page_title': 'Documentos y Formatos Descargables',
        'page_subtitle': 'Formularios, guías y planillas oficiales a disposición del público',
        'detail_btn_label': 'Descargar PDF',
    }

    def get_queryset(self):
        return Downloadable.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-publication_date')


class DownloadableManageView(LoginRequiredMixin, ListView):
    """Gestión de Descargables."""
    model = Downloadable
    template_name = 'core/generic_admin_list.html'
    paginate_by = 15
    extra_context = {
        'page_title': 'Gestión de Archivos Descargables',
        'page_subtitle': 'Administración de formularios, planillas y material de consulta pública',
        'header_icon': 'bi-file-earmark-arrow-down',
        'create_url': 'core:downloadable_create',
        'create_label': 'Nuevo Descargable',
        'update_url_name': 'core:downloadable_update',
        'delete_url_name': 'core:downloadable_delete',
    }

    def get_queryset(self):
        return Downloadable.objects.all().order_by('-publication_date')


class DownloadableCreateView(LoginRequiredMixin, CreateView):
    """Creación de Descargable."""
    model = Downloadable
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'pdf_file', 'publication_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_downloadables')
    extra_context = {
        'form_title': 'Subir Nuevo Documento Descargable',
        'form_subtitle': 'Adjunta archivos en formato PDF para el acceso libre de los ciudadanos',
        'form_icon': 'bi-cloud-upload',
        'submit_label': 'Publicar Documento',
        'cancel_url': reverse_lazy('core:manage_downloadables'),
    }

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.DOWNLOADABLE
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, "Documento descargable publicado.")
        return super().form_valid(form)


class DownloadableUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de Descargable."""
    model = Downloadable
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'pdf_file', 'publication_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_downloadables')
    extra_context = {
        'form_title': 'Editar Documento Descargable',
        'form_subtitle': 'Actualiza el título, resumen o reemplaza el archivo adjunto',
        'form_icon': 'bi-pencil-square',
        'submit_label': 'Guardar Cambios',
        'cancel_url': reverse_lazy('core:manage_downloadables'),
    }


class DownloadableDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de Descargable."""
    model = Downloadable
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_downloadables')
    extra_context = {
        'cancel_url': reverse_lazy('core:manage_downloadables'),
    }


# ============================================================
# 10. MÓDULO DE ACTIVIDADES Y SECCIÓN INSTITUCIONAL
# ============================================================

# --- ACTIVIDADES ---

class ActivityListView(ListView):
    """Listado público de actividades del Concejo."""
    model = Activity
    template_name = 'core/generic_cards_grid.html'
    context_object_name = 'object_list'
    paginate_by = 9
    extra_context = {
        'page_title': 'Actividades Institucionales',
        'page_subtitle': 'Trabajo comunitario, comisiones de calle y gestión en las parroquias',
        'detail_url_name': 'core:activity_detail',
        'detail_btn_label': 'Ver Detalle',
    }

    def get_queryset(self):
        return Activity.objects.filter(is_active=True, status=BaseContent.Status.PUBLISHED).order_by('-publication_date')


class ActivityDetailView(DetailView):
    """Detalle público de una actividad."""
    model = Activity
    template_name = 'core/generic_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_title'] = 'Otras Actividades'
        context['recent_items'] = Activity.objects.filter(is_active=True).exclude(pk=self.object.pk)[:4]
        context['back_url'] = reverse_lazy('core:activity_list')
        context['back_label'] = 'Volver a Actividades'
        return context


class ActivityManageView(LoginRequiredMixin, ListView):
    """Gestión administrativa de actividades."""
    model = Activity
    template_name = 'core/generic_admin_list.html'
    paginate_by = 15
    extra_context = {
        'page_title': 'Gestión de Actividades',
        'page_subtitle': 'Administra la publicación de jornadas e inspecciones de campo',
        'header_icon': 'bi-activity',
        'create_url': 'core:activity_create',
        'create_label': 'Nueva Actividad',
        'detail_url_name': 'core:activity_detail',
        'update_url_name': 'core:activity_update',
        'delete_url_name': 'core:activity_delete',
    }

    def get_queryset(self):
        return Activity.objects.all().order_by('-publication_date')


class ActivityCreateView(LoginRequiredMixin, CreateView):
    """Crear Actividad."""
    model = Activity
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'image', 'is_featured', 'publication_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_activities')
    extra_context = {
        'form_title': 'Registrar Nueva Actividad',
        'form_subtitle': 'Completa la información de la actividad institucional realizada',
        'form_icon': 'bi-journal-plus',
        'submit_label': 'Guardar Actividad',
        'cancel_url': reverse_lazy('core:manage_activities'),
    }

    def form_valid(self, form):
        form.instance.content_type = BaseContent.ContentType.ACTIVITY
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        messages.success(self.request, "Actividad creada exitosamente.")
        return super().form_valid(form)


class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    """Editar Actividad."""
    model = Activity
    template_name = 'core/generic_form.html'
    fields = ['title', 'summary', 'content', 'image', 'is_featured', 'publication_date', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_activities')
    extra_context = {
        'form_title': 'Editar Actividad',
        'form_subtitle': 'Modifica la información o fotografías de la actividad',
        'form_icon': 'bi-pencil-square',
        'submit_label': 'Guardar Cambios',
        'cancel_url': reverse_lazy('core:manage_activities'),
    }

    def form_valid(self, form):
        messages.success(self.request, "Actividad actualizada correctamente.")
        return super().form_valid(form)


class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar Actividad."""
    model = Activity
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('core:manage_activities')
    extra_context = {
        'cancel_url': reverse_lazy('core:manage_activities'),
    }


# --- EDICIÓN ADMINISTRATIVA SOBRE NOSOTROS ---

class AboutUsManageView(LoginRequiredMixin, ListView):
    """Gestión de textos de Quiénes Somos, Misión y Visión."""
    model = AboutUs
    template_name = 'core/generic_admin_list.html'
    paginate_by = 10
    extra_context = {
        'page_title': 'Gestión de Secciones Institucionales',
        'page_subtitle': 'Administra los bloques de Misión, Visión e Historia',
        'header_icon': 'bi-info-circle',
        'update_url_name': 'core:about_us_update',
    }


class AboutUsUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de sección institucional."""
    model = AboutUs
    template_name = 'core/generic_form.html'
    fields = ['title', 'content', 'image', 'is_active', 'status']
    success_url = reverse_lazy('core:manage_about_us')
    extra_context = {
        'form_title': 'Editar Sección Institucional',
        'form_subtitle': 'Actualiza los textos e imágenes oficiales de la institución',
        'form_icon': 'bi-pencil-square',
        'submit_label': 'Guardar Cambios',
        'cancel_url': reverse_lazy('core:manage_about_us'),
    }

    def form_valid(self, form):
        messages.success(self.request, "Información institucional actualizada.")
        return super().form_valid(form)
