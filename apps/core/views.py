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

from types import SimpleNamespace
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
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

# Modelos locales del módulo core
from .models import HomeContent, News, Chronicle, Category, Commission, Councilor
from .forms import NewsForm, CategoryForm, ChronicleForm, CommissionForm

User = get_user_model()


# ============================================================
# DATOS ESTÁTICOS DE RESPALDO (FALLBACK)
# ============================================================

NEWS_DATA = [
    {
        'id': 1,
        'title': 'Concejo Municipal fortalece labores de rescate de los «Ángeles de la Autopista»',
        'description': 'En el marco del desarrollo de la Sesión Ordinaria N° 55, el Concejo Municipal concretó la entrega formal de una antena de internet satelital Starlink al cuerpo paramédico y de rescate de los «Ángeles de la Autopista».',
        'image': 'https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=800',
        'date': '20 de agosto de 2026',
        'category': 'Social',
    },
    {
        'id': 2,
        'title': 'Nueva ordenanza para la protección del medio ambiente',
        'description': 'El Concejo Municipal aprobó una nueva ordenanza que regula el uso de plásticos de un solo uso en el municipio, con el objetivo de reducir la contaminación y proteger los espacios naturales.',
        'image': 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800',
        'date': '18 de agosto de 2026',
        'category': 'Cultura',
    },
    {
        'id': 3,
        'title': 'Jornada de atención al ciudadano en Rubio',
        'description': 'La alcaldía y el concejo municipal realizaron una jornada de atención al ciudadano en la plaza Bolívar de Rubio, donde se atendieron más de 200 personas en temas de salud, registro civil y servicios públicos.',
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
        'integrado por siete (7) concejales principales elegidos mediante el voto popular. Tiene como '
        'deber fundamental servir a los ciudadanos de Rubio y sus parroquias, garantizando canales '
        'efectivos de participación pública, contraloría social y el desarrollo de normativas que '
        'impulsen el bienestar colectivo.'
    ),
    'mission': (
        'Ejercer la función legislativa municipal mediante la creación, discusión y aprobación de '
        'ordenanzas locales, así como velar por el control político y la fiscalización de los recursos '
        'públicos de la Alcaldía del Municipio Junín, promoviendo de manera activa la participación '
        'ciudadana, la justicia social y el desarrollo sostenible de la comunidad andina.'
    ),
    'vision': (
        'Ser una institución legislativa de vanguardia, transparente, eficiente y cercana a los ciudadanos, '
        'reconocida en el Estado Táchira por su probidad en la gestión pública, la modernización de sus '
        'ordenanzas y su firme compromiso con la mejora de la calidad de vida, los servicios públicos '
        'y el rescate de la identidad histórica y cafetalera del municipio Junín.'
    ),
    'image_main': 'core/img/quienes_somos_junin.jpg'
}


# ============================================================
# 1. PORTAL PÚBLICO GENERAL (HOME & INSTITUCIONAL)
# ============================================================

class HomeView(TemplateView):
    """
    Vista principal de la portada web.
    Combina datos de Base de Datos (documentos, gacetas, carrusel, crónicas)
    con respaldo de datos estáticos cuando la BD está vacía.
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Documentos y gacetas recientes
        try:
            context['documentos_destacados'] = Document.objects.select_related(
                'gazette', 'document_type'
            ).order_by('-publication_date')[:2]
            context['ultimas_gacetas'] = Gazette.objects.all()[:3]
        except Exception:
            context['documentos_destacados'] = []
            context['ultimas_gacetas'] = []

        # 2. Noticias para el carrusel principal
        try:
            context['carousel_news'] = News.objects.filter(is_active=True).order_by('-created_at')[:5]
        except Exception:
            context['carousel_news'] = []

        # 3. Crónicas municipales recientes
        try:
            context['chronicles'] = Chronicle.objects.filter(is_active=True).order_by('-created_at')[:3]
        except Exception:
            context['chronicles'] = []

        # 4. Listado secundario de noticias
        try:
            news_qs = News.objects.filter(is_active=True).order_by('-created_at')
            context['news_list'] = news_qs[:3] if news_qs.exists() else NEWS_DATA
        except Exception:
            context['news_list'] = NEWS_DATA

        # 5. Listado de Concejales para la portada
        try:
            context['councilors'] = Councilor.objects.all()
        except Exception:
            context['councilors'] = []

        return context


class AboutUsView(TemplateView):
    """
    Vista pública institucional ('Quiénes Somos').
    Unifica la información institucional con respaldo de datos locales.
    """
    template_name = 'core/about_us.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about_data'] = ABOUT_US_DATA
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

    news_list = News.objects.filter(is_active=True).order_by('-created_at')
    categories = Category.objects.all()

    if query:
        news_list = news_list.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query)
        )

    if date_query:
        try:
            news_list = news_list.filter(created_at__date=date_query)
        except (ValidationError, ValueError):
            # Si el formato de la fecha es inválido, ignoramos el filtro en lugar de romper con un Error 500
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
    """
    Vista de lectura individual de noticia.
    Soporta carga desde BD y fallback estático de demostración.
    """
    try:
        news_item = News.objects.get(pk=pk, is_active=True)
        if news_item.category:
            related_news = News.objects.filter(
                is_active=True,
                category=news_item.category
            ).exclude(pk=pk).order_by('-created_at')[:3]
        else:
            related_news = News.objects.filter(is_active=True).exclude(pk=pk).order_by('-created_at')[:3]

    except News.DoesNotExist:
        # Fallback para datos de prueba si el ID coincide
        fallback = next((item for item in NEWS_DATA if item['id'] == pk), None)
        if fallback:
            news_item = SimpleNamespace(
                id=fallback['id'],
                title=fallback['title'],
                summary=fallback['description'],
                content=fallback['description'],
                image=SimpleNamespace(url=fallback['image']) if fallback.get('image') else None,
                category=SimpleNamespace(name=fallback['category']) if fallback.get('category') else None,
                created_at=fallback['date'],
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


@login_required
def manage_news_frontend(request):
    """Panel de gestión interna: creación y listado de noticias."""
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia creada exitosamente.')
            return redirect('core:manage_news_frontend')
    else:
        form = NewsForm()

    news_list = News.objects.all().order_by('-created_at')
    context = {'form': form, 'news_list': news_list}
    return render(request, 'core/manage_news.html', context)


@login_required
def update_news_frontend(request, pk):
    """Panel de gestión interna: edición de noticia."""
    news_item = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('core:manage_news_frontend')
    else:
        form = NewsForm(instance=news_item)

    context = {'form': form, 'news_item': news_item}
    return render(request, 'core/update_news.html', context)


@login_required
def delete_news_frontend(request, pk):
    """Panel de gestión interna: eliminación de noticia."""
    news_item = get_object_or_404(News, pk=pk)
    if request.method == 'POST':
        news_item.delete()
        messages.success(request, 'Noticia eliminada correctamente.')
        return redirect('core:manage_news_frontend')

    return render(request, 'core/delete_news.html', {'news_item': news_item})


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

@login_required
def manage_categories_frontend(request):
    """Listado y creación de categorías."""
    categories = Category.objects.all()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada exitosamente.")
            return redirect('core:manage_categories_frontend')
    else:
        form = CategoryForm()

    context = {'form': form, 'categories': categories}
    return render(request, 'core/manage_categories.html', context)


@login_required
def update_category_frontend(request, pk):
    """Edición de categoría existente."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada exitosamente.")
            return redirect('core:manage_categories_frontend')
    else:
        form = CategoryForm(instance=category)

    context = {'form': form, 'category': category}
    return render(request, 'core/update_category.html', context)


@login_required
def delete_category_frontend(request, pk):
    """Eliminación de categoría."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Categoría eliminada exitosamente.")
        return redirect('core:manage_categories_frontend')

    context = {'category': category}
    return render(request, 'core/delete_category.html', context)


# ============================================================
# 6. MÓDULO DE COMISIONES PERMANENTES (PÚBLICO Y GESTIÓN)
# ============================================================

class CommissionsView(ListView):
    """Vista pública de las Comisiones Permanentes de Trabajo."""
    model = Commission
    template_name = 'core/commissions.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        return Commission.objects.select_related('president', 'vice_president', 'vocal').order_by('number')


class CommissionAdminListView(LoginRequiredMixin, ListView):
    """Listado administrativo de comisiones."""
    model = Commission
    template_name = 'core/commission_admin_list.html'
    context_object_name = 'commissions'

    def get_queryset(self):
        return Commission.objects.select_related('president', 'vice_president', 'vocal').order_by('number')


class CommissionCreateView(LoginRequiredMixin, CreateView):
    """Creación de comisión."""
    model = Commission
    form_class = CommissionForm
    template_name = 'core/commission_form.html'
    success_url = reverse_lazy('core:commission_admin_list')


class CommissionUpdateView(LoginRequiredMixin, UpdateView):
    """Edición de comisión existente."""
    model = Commission
    form_class = CommissionForm
    template_name = 'core/commission_form.html'
    success_url = reverse_lazy('core:commission_admin_list')


class CommissionDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de comisión."""
    model = Commission
    template_name = 'core/commission_confirm_delete.html'
    success_url = reverse_lazy('core:commission_admin_list')


# ============================================================
# 7. MÓDULO DE CONCEJALES (PÚBLICO Y GESTIÓN)
# ============================================================

class CouncilorListView(ListView):
    """Listado público de concejales y directiva activa."""
    model = HomeContent
    template_name = 'core/councilors_public_list.html'
    context_object_name = 'councilors'

    def get_queryset(self):
        return HomeContent.objects.filter(
            content_type='COUNCILOR',
            is_active=True,
            status='PUBLISHED'
        ).order_by('order', 'title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['syndicate'] = SYNDICATE_DATA
        return context


class CouncilorDetailView(DetailView):
    """Detalle del perfil público de un concejal."""
    model = HomeContent
    template_name = 'core/councilor_detail.html'
    context_object_name = 'councilor'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return HomeContent.objects.filter(content_type='COUNCILOR', is_active=True)


class CouncilorCreateView(LoginRequiredMixin, CreateView):
    """Registro administrativo de un concejal."""
    model = HomeContent
    template_name = 'core/councilor_form.html'
    fields = ['title', 'author', 'summary', 'content', 'image', 'social_media_url', 'order', 'is_active', 'status']
    success_url = reverse_lazy('core:councilors')

    def form_valid(self, form):
        form.instance.content_type = 'COUNCILOR'
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        return super().form_valid(form)


class CouncilorUpdateView(LoginRequiredMixin, UpdateView):
    """Edición administrativa de un concejal."""
    model = HomeContent
    template_name = 'core/councilor_form.html'
    fields = ['title', 'author', 'summary', 'content', 'image', 'social_media_url', 'order', 'is_active', 'status']
    success_url = reverse_lazy('core:councilors')


class CouncilorDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación administrativa de un concejal."""
    model = HomeContent
    template_name = 'core/councilor_confirm_delete.html'
    success_url = reverse_lazy('core:councilors')


# ============================================================
# 8. MÓDULO DE LEGISLATURAS (PÚBLICO Y GESTIÓN)
# ============================================================

class LegislatureListView(ListView):
    """Listado público de Legislaturas y Períodos Legislativos."""
    model = HomeContent
    template_name = 'core/legislatures_list.html'
    context_object_name = 'legislatures'

    def get_queryset(self):
        return HomeContent.objects.filter(
            content_type=HomeContent.ContentTypes.LEGISLATURE,
            is_active=True,
            status=HomeContent.Status.PUBLISHED
        ).order_by('order', '-publication_date')


class LegislatureCreateView(LoginRequiredMixin, CreateView):
    """Creación administrativa de una nueva Legislatura."""
    model = HomeContent
    template_name = 'core/legislature_form.html'
    fields = [
        'title', 'author', 'summary', 'content', 'image',
        'pdf_file', 'show_pdf_inline', 'order', 'is_active', 'status'
    ]
    success_url = reverse_lazy('core:legislatures_list')

    def form_valid(self, form):
        form.instance.content_type = HomeContent.ContentTypes.LEGISLATURE
        if self.request.user.is_authenticated:
            form.instance.created_by = self.request.user
        return super().form_valid(form)


class LegislatureUpdateView(LoginRequiredMixin, UpdateView):
    """Edición administrativa de una Legislatura."""
    model = HomeContent
    template_name = 'core/legislature_form.html'
    fields = [
        'title', 'author', 'summary', 'content', 'image',
        'pdf_file', 'show_pdf_inline', 'order', 'is_active', 'status'
    ]
    success_url = reverse_lazy('core:legislatures_list')


class LegislatureDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminación de una Legislatura."""
    model = HomeContent
    template_name = 'core/legislature_confirm_delete.html'
    success_url = reverse_lazy('core:legislatures_list')