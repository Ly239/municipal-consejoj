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
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin #Para autenticacion de usuario
from django.contrib.auth import authenticate,login, get_user_model,logout
from django.views import View
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.contrib import messages                      # <- necesario para mostrar mensajes
from documents.models import Document, Gazette
# Importamos los modelos proxy para el contenido dinámico del home
from .models import Councilor, News, Carousel, AboutUs

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
        'years': '1989 - 1992', # El primer período de alcaldes electos arrancó en 1989
        'mayor': 'Juan de Dios Cañas',  # Primer alcalde electo directamente en Junín
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
        'years': '1995 - 2000', # Período extendido por transición constitucional
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
        'years': '2005 - 2013',  # Período extendido nacionalmente
        'mayor': 'Juan Peñaloza / Mercedes Chapeta', # Nombre corregido: Chapeta
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
        'years': '2021 - Presente', # Gestión legislativa bajo la alcaldía de Jackson Carrillo
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



class NewsDetailView(TemplateView):
    """Vista para el detalle de una noticia."""
    template_name = 'core/news_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        news_id = self.kwargs.get('pk')

        # Obtener la noticia actual (DB o estática)
        try:
            news = News.objects.get(pk=news_id)
            context['news'] = {
                'id': news.id,
                'title': news.title,
                'description': news.description,
                'image': news.image.url if news.image else 'core/img/default_news.jpg',
                'date': news.date.strftime('%d de %B de %Y'),
                'category': news.content_type,
            }
        except Exception:
            for item in NEWS_DATA:
                if item['id'] == news_id:
                    context['news'] = item
                    break

        # Últimas noticias (excluyendo la actual)
        try:
            latest = News.objects.exclude(pk=news_id).order_by('-publication_date')[:5]
            context['latest_news'] = [
                {
                    'id': new.id,
                    'title': new.title,
                    'date': new.date.strftime('%d/%m/%Y'),
                }
                for new in latest
            ]
        except Exception:
            context['latest_news'] = [
                {'id': item['id'], 'title': item['title'], 'date': item['date']}
                for item in NEWS_DATA if item['id'] != news_id
            ][:5]

        # Fallback si no hay noticias
        if not context.get('latest_news'):
            context['latest_news'] = [
                {'id': item['id'], 'title': item['title'], 'date': item['date']}
                for item in NEWS_DATA if item['id'] != news_id
            ][:5]

        return context


class CouncilorsView(TemplateView):
    """Vista para la página de concejales (estática con datos de ejemplo)."""
    template_name = 'core/councilors.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['councilors'] = COUNCILORS_DATA
        context['syndicate'] = SYNDICATE_DATA
        return context


class AboutUsView(TemplateView):
    template_name = 'core/about_us.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['legislatures'] = LEGISLATURES_DATA  # Pasa los datos reales
        return context



def HomeView(request):
    """Vista principal que combina datos dinámicos (Proxy Models) y estáticos de ejemplo."""
    context = {}

    # Carga de documentos y gacetas desde la BD (si existen)
    try:
        context['documentos_destacados'] = Document.objects.select_related('gazette', 'document_type').order_by('-publication_date')[:2]
        context['ultimas_gacetas'] = Gazette.objects.all()[:3]
    except Exception:
        context['documentos_destacados'] = []
        context['ultimas_gacetas'] = []

    # Carga de noticias (Proxy Models o fallback estático)
    try:
        news_qs = News.objects.all()
        context['news_list'] = news_qs[:3] if news_qs.exists() else NEWS_DATA
    except Exception:
        context['news_list'] = NEWS_DATA

    # Otros contenidos del Home (Proxy Models)
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

    return render(request, 'core/home.html', context)



class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # KPI Cards
        context['total_documents'] = Document.objects.count()
        context['total_gazettes'] = Gazette.objects.count()
        context['total_users'] = User.objects.count()

        # Papelera
        from common.views import TRASH_MODELS
        trash_count = 0
        for model in TRASH_MODELS:
            trash_count += model.all_objects.filter(deleted_at__isnull=False).count()
        context['total_trash'] = trash_count

        # Documentos recientes (últimos 5)
        context['recent_documents'] = Document.objects.select_related(
            'document_type', 'gazette'
        ).order_by('-created_at')[:5]

        # Datos para el gráfico
        context['approved_count'] = Document.objects.filter(is_approved=True).count()
        context['pending_count'] = Document.objects.filter(is_approved=False).count()

        return context


