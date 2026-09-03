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



# Datos estaticos de ejemplo para noticia (for demo without DB)
NEWS_DATA = [
    {
        'id': 1,
        'title': 'Concejo Municipal fortalece labores de rescate de los «Ángeles de la Autopista»',
        'description': 'En el marco del desarrollo de la Sesión Ordinaria N° 55, el Concejo Municipal concretó la entrega formal de una antena de internet satelital Starlink al cuerpo paramédico y de rescate de los «Ángeles de la Autopista».',
        'image': 'core/img/noticia1.jpg',
        'date': '20 de agosto de 2026',
        'category': 'Social',
    },
    {
        'id': 2,
        'title': 'Nueva ordenanza para la protección del medio ambiente',
        'description': 'El Concejo Municipal aprobó una nueva ordenanza que regula el uso de plásticos de un solo uso en el municipio, con el objetivo de reducir la contaminación y proteger los espacios naturales.',
        'image': 'core/img/noticia2.jpg',
        'date': '18 de agosto de 2026',
        'category': 'Cultura',
    },
    {
        'id': 3,
        'title': 'Jornada de atención al ciudadano en Rubio',
        'description': 'La alcaldía y el concejo municipal realizaron una jornada de atención al ciudadano en la plaza Bolívar de Rubio, donde se atendieron más de 200 personas en temas de salud, registro civil y servicios públicos.',
        'image': 'core/img/noticia3.jpg',
        'date': '15 de agosto de 2026',
        'category': 'Salud',
    },
]



class NewsDetailView(TemplateView):
    template_name = 'core/news_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        news_id = self.kwargs.get('pk')
        
        # 1. Obtener la noticia actual (DB o estática)
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

        # 2. Obtener últimas noticias (Siempre desde NEWS_DATA para la demo)
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
            # Fallback a datos estáticos SIEMPRE
            context['latest_news'] = [
                {'id': item['id'], 'title': item['title'], 'date': item['date']}
                for item in NEWS_DATA if item['id'] != news_id
            ][:5]

        # Si no hay noticias en latest_news, usar todas las estáticas
        if not context.get('latest_news'):
            context['latest_news'] = [
                {'id': item['id'], 'title': item['title'], 'date': item['date']}
                for item in NEWS_DATA if item['id'] != news_id
            ][:5]

        return context


def HomeView(request):
    """Tabla Principal de los modelos dinámicos"""
    context = {}

    # 1. Documentos desde BD (if any)
    try:
        context['documentos_destacados'] = Document.objects.select_related('gazette', 'document_type').order_by('-publication_date')[:2]
        context['ultimas_gacetas'] = Gazette.objects.all()[:3]
    except Exception:
        context['documentos_destacados'] = []
        context['ultimas_gacetas'] = []

    # 2. Noticias (or static data for demo)
    try:
        context['news_list'] = News.objects.all()[:3]
        if not context['news_list']:
            context['news_list'] = NEWS_DATA  # Fallback to static data
    except Exception:
        context['news_list'] = NEWS_DATA

    # 3. Otros proxy models (if any)
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


