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


def HomeView(request):
    """Vista principal combinando documentos previos y el nuevo contenido dinámico (Proxy Models)."""
    context = {}

    # 1. Carga segura de documentos y gacetas anteriores
    try:
        context['documentos_destacados'] = Document.objects.select_related('gazette', 'document_type').order_by('-publication_date')[:2]
        context['ultimas_gacetas'] = Gazette.objects.all()[:3]
    except Exception as e:
        messages.error(request, f'Error al cargar los documentos recientes: {e}')
        context['documentos_destacados'] = []
        context['ultimas_gacetas'] = []

    # 2. Carga segura del contenido dinámico del Home usando Proxy Models
    try:
        context['councilors'] = Councilor.objects.all()
    except Exception:
        context['councilors'] = []

    try:
        context['news_list'] = News.objects.all()[:5]  # Últimas 5 noticias
    except Exception:
        context['news_list'] = []

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


