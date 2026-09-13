"""
Copyright [2026] [Proyecto universitario]

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
from django.contrib.auth.mixins import LoginRequiredMixin #Para autenticacion de usuario
from django.contrib.auth import authenticate,login, get_user_model,logout
from django.views import View
from django.views.generic import TemplateView, ListView
from django.core.paginator import Paginator
from django.contrib import messages                      # <- necesario para mostrar mensajes
from documents.models import Document, Gazette


# Imports de modelos de core (unificados tras merge home-core)
from .models import (
    HomeCarouselNews, Category, Chronicle,
    Councilor, News, Carousel, AboutUs,
)
from .forms import HomeCarouselNewsForm, CategoryForm, ChronicleForm

User = get_user_model()



# ============================================================
# DATOS DE EJEMPLO PARA DEMO ESTÁTICA (SIN BD)
# ============================================================

# Noticias de ejemplo (con imágenes de Unsplash)
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


# Datos reales de Concejales del Municipio Junín (con fotos de Unsplash)
COUNCILORS_DATA = [
    # Bloque de Presidencia
    {
        'name': 'Danny Carrillo',
        'position': 'Presidente del Concejo Municipal',
        'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
        'bio': 'Abogado comprometido con el desarrollo civil de Rubio. Lidera el parlamento municipal con un enfoque en la modernización institucional y el fortalecimiento de la legislación vecinal.'
    },
    {
        'name': 'F. Kempes',
        'position': 'Vicepresidente del Concejo Municipal',
        'image': 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400',
        'bio': 'Líder social enfocado en la articulación de las comisiones del concejo y el seguimiento parlamentario. Promueve el desarrollo integral de las comunidades rurales del municipio.'
    },
    {
        'name': 'Johan Lizcano',
        'position': 'Concejal Principal',
        'image': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=400',
        'bio': 'Vocero comunitario con trayectoria en la fiscalización de la gestión local. Centra sus esfuerzos en la mejora del transporte, la infraestructura y los servicios públicos andinos.'
    },
    # Bloque de Comisiones
    {
        'name': 'Rubén Manrique',
        'position': 'Concejal Principal',
        'image': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400',
        'bio': 'Planificador enfocado en el desarrollo económico y comercial del municipio Junín. Su meta principal es el rescate del potencial cafetalero e histórico de la región.'
    },
    {
        'name': 'Sonia Mendoza',
        'position': 'Concejal Principal',
        'image': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400',
        'bio': 'Docente y defensora comunitaria. Dedica su actividad legislativa al impulso de programas educativos, culturales y de protección a sectores vulnerables de Rubio.'
    },
    {
        'name': 'Marco Rincón',
        'position': 'Concejal Principal',
        'image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
        'bio': 'Promotor vecinal enfocado en la transparencia presupuestaria. Trabaja activamente en las comisiones técnicas orientadas a la contraloría social municipal.'
    },
    {
        'name': 'Concejal por incorporar',
        'position': 'Concejal Suplente / Incorporado',
        'image': 'https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?w=400',
        'bio': 'Apoya las funciones legislativas del bloque de comisiones y participa activamente en el despliegue del parlamentarismo de calle en las parroquias del municipio.'
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


# Historial legislativo real del Municipio Junín (Táchira) para el About Us
LEGISLATURES_DATA = [
    {
        'id': 'I',
        'years': '1989 - 1992',
        'mayor': 'Juan de Dios Cañas',
        'members': [
            {'name': 'Armando Bautista', 'party': 'AD'},
            {'name': 'Sonia Hernán de Bastos', 'party': 'AD'},
            {'name': 'José Omar Boada', 'party': 'AD'},
            {'name': 'Luis Antonio Ruda', 'party': 'AD'},
            {'name': 'Félix Campero Sánchez', 'party': 'AD'},
            {'name': 'Juan Abello González', 'party': 'COPEI'},
        ]
    },
    {
        'id': 'II',
        'years': '1992 - 1995',
        'mayor': 'Pedro Fernández',
        'members': [
            {'name': 'Nelson Flores Galvis', 'party': 'COPEI'},
            {'name': 'Evaristo Monsalve', 'party': 'COPEI'},
            {'name': 'Juan Abello González', 'party': 'COPEI'},
            {'name': 'Sonia Hernán de Bastos', 'party': 'AD'},
            {'name': 'Marcos Moreno', 'party': 'AD'},
        ]
    },
    {
        'id': 'III',
        'years': '1995 - 2000',
        'mayor': 'Gonzalo Fuentes La Cruz',
        'members': [
            {'name': 'Gerardo Carrero', 'party': 'AD'},
            {'name': 'Héctor Cabrera', 'party': 'AD'},
            {'name': 'Marcos Moreno', 'party': 'AD'},
            {'name': 'Pedro Chirinos', 'party': 'COPEI'},
            {'name': 'Yaneth de Carrillo', 'party': 'COPEI'},
        ]
    },
    {
        'id': 'IV',
        'years': '2000 - 2005',
        'mayor': 'Luis Valladares',
        'members': [
            {'name': 'César Vera', 'party': 'MVR'},
            {'name': 'Luis Sandoval', 'party': 'MVR'},
            {'name': 'María Elena Ruiz', 'party': 'AD'},
            {'name': 'Jorge Salcedo', 'party': 'COPEI'},
        ]
    },
    {
        'id': 'V',
        'years': '2005 - 2013',
        'mayor': 'Juan Peñaloza / Mercedes Chapeta',
        'members': [
            {'name': 'José Araujo', 'party': 'PSUV'},
            {'name': 'Gladys Yáñez', 'party': 'PSUV'},
            {'name': 'Yobel Sandoval', 'party': 'COPEI'},
            {'name': 'Walter Chacón', 'party': 'AD'},
        ]
    },
    {
        'id': 'VI',
        'years': '2013 - 2018',
        'mayor': 'Yobel Sandoval',
        'members': [
            {'name': 'Danny Carrillo', 'party': 'COPEI'},
            {'name': 'Sonia Mendoza', 'party': 'AD'},
            {'name': 'Marcos Rincón', 'party': 'MUD'},
            {'name': 'Johan Lizcano', 'party': 'MUD'},
        ]
    },
    {
        'id': 'VII',
        'years': '2018 - 2021',
        'mayor': 'Ángel Márquez',
        'members': [
            {'name': 'Herlany Rivas', 'party': 'PSUV'},
            {'name': 'Rubén Manrique', 'party': 'PSUV'},
            {'name': 'Elizabeth Martínez', 'party': 'PSUV'},
        ]
    },
    {
        'id': 'VIII',
        'years': '2021 - Presente',
        'mayor': 'Jackson Carrillo',
        'members': [
            {'name': 'Danny Carrillo', 'party': 'MUD'},
            {'name': 'F. Kempes', 'party': 'MUD'},
            {'name': 'Johan Lizcano', 'party': 'MUD'},
            {'name': 'Sonia Mendoza', 'party': 'MUD'},
            {'name': 'Marco Rincón', 'party': 'MUD'},
            {'name': 'Rubén Manrique', 'party': 'Alianza Dem.'},
        ]
    }
]


# Lista oficial de las 6 comisiones reales de Junín con ID de control para los Modales
COMMISSIONS_DATA = [
    {
        'id': 1,
        'emoji': '🚰',
        'title': 'Comisión de Servicios Públicos y Espectáculos',
        'description': 'Encargada de vigilar la distribución de agua potable, electricidad, vialidad, aseo urbano y transporte en el casco central de Rubio y sus aldeas.',
        'image': 'core/img/comision_servicios.png',
        'president': 'Johan Lizcano',
        'vicepresident': 'Franklin Kempes',
        'vocal': 'Marco Rincón'
    },
    {
        'id': 2,
        'emoji': '☕',
        'title': 'Comisión de Economía y Desarrollo Cafetalero',
        'description': 'Enfocada en el reimpulso comercial, el emprendimiento y el rescate del potencial histórico agrícola del café de la región andina.',
        'image': 'core/img/comision_economia.jpg',
        'president': 'Rubén Manrique',
        'vicepresident': 'Danny Carrillo',
        'vocal': 'Sonia Mendoza'
    },
    {
        'id': 3,
        'emoji': '🎓',
        'title': 'Comisión de Educación, Cultura y Deporte',
        'description': 'Encargada de coordinar los programas de becas locales, preservación del patrimonio colonial, eventos deportivos y apoyo a las escuelas de Junín.',
        'image': 'core/img/comision_educacion.jpg',
        'president': 'Sonia Mendoza',
        'vicepresident': 'Johan Lizcano',
        'vocal': 'Luis Sandoval'
    },
    {
        'id': 4,
        'emoji': '🛡️',
        'title': 'Comisión de Seguridad Ciudadana y Vialidad',
        'description': 'Trabaja de la mano con la Policía y Protección Civil para el diseño de planes de prevención vecinal, semaforización y leyes de convivencia.',
        'image': 'core/img/comision_seguridad.jpg',
        'president': 'Marco Rincón',
        'vicepresident': 'Rubén Manrique',
        'vocal': 'Danny Carrillo'
    },
    {
        'id': 5,
        'emoji': '⚖️',
        'title': 'Comisión de Legislación y Contraloría',
        'description': 'Supervisa los aspectos jurídicos de las nuevas ordenanzas fiscales, los impuestos y ejerce la auditoría presupuestaria de la Alcaldía de Junín.',
        'image': 'core/img/comision_legislacion.png',
        'president': 'Danny Carrillo',
        'vicepresident': 'Sonia Mendoza',
        'vocal': 'Johan Lizcano'
    },
    {
        'id': 6,
        'emoji': '⛰️',
        'title': 'Comisión de Asuntos Parroquiales y Frontera',
        'description': 'Mapea y canaliza las peticiones de los sectores rurales y fronterizos, impulsando el parlamentarismo de calle en la Parroquia Bramón y Quinimarí.',
        'image': 'core/img/comision_parroquias.png',
        'president': 'Franklin Kempes',
        'vicepresident': 'Marco Rincón',
        'vocal': 'Rubén Manrique'
    }
]


# Información oficial de identidad para el apartado "Quiénes Somos" del Municipio Junín
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


# ==========================================
# 1. VISTAS DEL PORTAL PÚBLICO (FRONTEND)
# ==========================================
class NewsDetailView(TemplateView):
    """Vista de detalle de noticia. Lee de BD; si no existe, usa datos de demo estática."""
    template_name = 'core/news_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        news_id = self.kwargs.get('pk')

        # 1. Intentar cargar desde BD
        try:
            context['news_item'] = News.objects.get(pk=news_id)
        except News.DoesNotExist:
            # 2. Fallback estático (solo si no está en BD)
            fallback = next((item for item in NEWS_DATA if item['id'] == news_id), None)
            if fallback:
                context['news_item'] = self._adapt_static_item(fallback)

        # 3. Noticias relacionadas
        try:
            context['related_news'] = News.objects.exclude(pk=news_id).order_by('-publication_date')[:3]
        except Exception:
            context['related_news'] = []

        return context

    @staticmethod
    def _adapt_static_item(item):
        """Adapta un dict de NEWS_DATA a un objeto compatible con el template."""
        return SimpleNamespace(
            id=item['id'],
            title=item['title'],
            summary=item['description'],
            content=item['description'],
            image={'url': item['image']},
            category={'name': item['category']},
            created_at=None,
            pdf_file=None,
            show_pdf_inline=False,
            social_media_url=None,
        )


class CouncilorsView(TemplateView):
    """Vista para la página de concejales (estática con datos de ejemplo)."""
    template_name = 'core/councilors.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['councilors'] = COUNCILORS_DATA
        context['syndicate'] = SYNDICATE_DATA
        return context


class CommissionsView(TemplateView):
    template_name = 'core/commissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['commissions'] = COMMISSIONS_DATA
        return context


class AboutUsView(TemplateView):
    template_name = 'core/about_us.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about_data'] = ABOUT_US_DATA
        context['legislatures'] = LEGISLATURES_DATA
        return context



class HomeView(TemplateView):
    """
    Vista principal del Home.
    Combina datos de BD (documentos, gacetas, carrusel, crónicas)
    con datos estáticos de ejemplo y modelos proxy.
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Documentos y gacetas (desde BD, si existen)
        try:
            context['documentos_destacados'] = Document.objects.select_related(
                'gazette', 'document_type'
            ).order_by('-publication_date')[:2]
            context['ultimas_gacetas'] = Gazette.objects.all()[:3]
        except Exception:
            context['documentos_destacados'] = []
            context['ultimas_gacetas'] = []

        # 2. Carrusel de noticias activas (integración home-core)
        try:
            context['carousel_news'] = HomeCarouselNews.objects.filter(is_active=True)
        except Exception:
            context['carousel_news'] = []

        # 3. Crónicas municipales recientes (integración home-core)
        try:
            context['chronicles'] = Chronicle.objects.filter(is_active=True)[:3]
        except Exception:
            context['chronicles'] = []

        # 4. Noticias (Proxy Models o fallback estático)
        try:
            news_qs = News.objects.all()
            context['news_list'] = news_qs[:3] if news_qs.exists() else NEWS_DATA
        except Exception:
            context['news_list'] = NEWS_DATA

        # 5. Otros contenidos del Home (Proxy Models)
        try:
            context['councilors'] = Councilor.objects.all()
        except Exception:
            context['councilors'] = []

        try:
            context['carousel_items'] = Carousel.objects.all()
        except Exception:
            context['carousel_items'] = []

        try:
            context['about_us'] = AboutUs.objects.first()
        except Exception:
            context['about_us'] = None

        return context

##################################################################
# Cambios compañero colaborador 2 (Home dinámico)
# Recomendación usar CVB (Vistas Basadas eb Clases)


def news_public_list_frontend(request):
    """Listado público de noticias con filtros por texto, fecha y categoría."""
    query = request.GET.get('q', '')
    date_query = request.GET.get('date', '')
    category_slug = request.GET.get('category', '')

    news_list = HomeCarouselNews.objects.all()
    categories = Category.objects.all()

    if query:
        news_list = news_list.filter(Q(title__icontains=query) | Q(summary__icontains=query))
    if date_query:
        news_list = news_list.filter(created_at__date=date_query)
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
    """Vista detallada de una noticia individual del carrusel (integración home-core)."""
    news_item = get_object_or_404(HomeCarouselNews, pk=pk, is_active=True)

    if news_item.category:
        related_news = HomeCarouselNews.objects.filter(
            is_active=True,
            category=news_item.category
        ).exclude(pk=pk)[:3]
    else:
        related_news = HomeCarouselNews.objects.filter(is_active=True).exclude(pk=pk)[:3]

    context = {
        'news_item': news_item,
        'related_news': related_news,
    }
    return render(request, 'core/news_detail.html', context)



def chronicle_public_list(request):
    """Listado público de crónicas históricas activas."""
    chronicles = Chronicle.objects.filter(is_active=True)
    return render(request, 'core/chronicles_public_list.html', {'chronicles': chronicles})


def chronicle_detail(request, slug):
    """Vista de lectura detallada para una crónica específica."""
    chronicle = get_object_or_404(Chronicle, slug=slug, is_active=True)
    recent_chronicles = Chronicle.objects.filter(is_active=True).exclude(pk=chronicle.pk)[:3]
    return render(request, 'core/chronicles_detail.html', {
        'chronicle': chronicle,
        'recent_chronicles': recent_chronicles
    })


# --- Gestión de Noticias ---

def manage_news_frontend(request):
    """[ROLES]: Punto de integración para administradores del módulo de Noticias."""
    if request.method == 'POST':
        form = HomeCarouselNewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia de carrusel creada exitosamente.')
            return redirect('core:manage_news_frontend')
    else:
        form = HomeCarouselNewsForm()

    news_list = HomeCarouselNews.objects.all()
    context = {'form': form, 'news_list': news_list}
    return render(request, 'core/manage_news.html', context)


def update_news_frontend(request, pk):
    """Edición de una noticia existente en el carrusel."""
    news_item = get_object_or_404(HomeCarouselNews, pk=pk)
    if request.method == 'POST':
        form = HomeCarouselNewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia actualizada exitosamente.')
            return redirect('core:manage_news_frontend')
    else:
        form = HomeCarouselNewsForm(instance=news_item)

    context = {'form': form, 'news_item': news_item}
    return render(request, 'core/update_news.html', context)


def delete_news_frontend(request, pk):
    """Eliminación lógica o física de una noticia del carrusel."""
    news_item = get_object_or_404(HomeCarouselNews, pk=pk)
    if request.method == 'POST':
        news_item.delete()
        messages.success(request, 'Noticia eliminada correctamente.')
        return redirect('core:manage_news_frontend')

    return render(request, 'core/delete_news.html', {'news_item': news_item})


# --- Gestión de Crónicas (Unificada) ---

def manage_chronicles(request):
    """Panel interno de operador para listar y administrar todas las crónicas."""
    chronicles = Chronicle.objects.all()
    return render(request, 'core/manage_chronicles.html', {'chronicles': chronicles})


def save_chronicle(request, pk=None):
    """Vista unificada para Crear o Editar una crónica utilizando save_chronicles.html."""
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


def delete_chronicle(request, pk):
    """Acción rápida para eliminar una crónica del sistema."""
    chronicle = get_object_or_404(Chronicle, pk=pk)
    chronicle.delete()
    messages.success(request, "Crónica eliminada correctamente.")
    return redirect('core:manage_chronicles')


# --- Gestión de Categorías ---

def manage_categories_frontend(request):
    """Listado y creación de categorías para noticias/documentos."""
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


def update_category_frontend(request, pk):
    """Edición de una categoría existente."""
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


def delete_category_frontend(request, pk):
    """Eliminación de una categoría del sistema."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Categoría eliminada exitosamente.")
        return redirect('core:manage_categories_frontend')

    context = {'category': category}
    return render(request, 'core/delete_category.html', context)

#################################################################



# ==========================================
# 2. PANEL DE ADMINISTRACIÓN / GESTIÓN INTERNA
# ==========================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """Panel de control principal para usuarios autenticados (KPIs y estadísticas)."""
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_documents'] = Document.objects.count()
        context['total_gazettes'] = Gazette.objects.count()
        context['total_users'] = User.objects.count()

        from common.views import TRASH_MODELS
        trash_count = 0
        for model in TRASH_MODELS:
            trash_count += model.all_objects.filter(deleted_at__isnull=False).count()
        context['total_trash'] = trash_count

        context['recent_documents'] = Document.objects.select_related(
            'document_type', 'gazette'
        ).order_by('-created_at')[:5]

        context['approved_count'] = Document.objects.filter(is_approved=True).count()
        context['pending_count'] = Document.objects.filter(is_approved=False).count()

        return context