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
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin #Para autenticacion de usuario
from django.contrib.auth import authenticate,login, get_user_model,logout
from django.views import View
from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.contrib import messages                      # <- necesario para mostrar mensajes
from documents.models import Document, Gazette
from .models import HomeCarouselNews, MunicipalChronicle, Category
from .forms import HomeCarouselNewsForm, MunicipalChronicleForm, CategoryForm
User = get_user_model()





def HomeView(request):
    try:
        # Consultas dinámicas para la base de datos (Documentos y Gacetas previos)
        documentos_destacados = Document.objects.select_related('gazette', 'document_type').order_by('-publication_date')[:2]
        ultimas_gacetas = Gazette.objects.all()[:3]

        # Nuevas consultas dinámicas para el Carrusel de Noticias y las Crónicas Municipales
        carousel_news = HomeCarouselNews.objects.filter(is_active=True)
        chronicles = MunicipalChronicle.objects.filter(is_published=True)[:3]

        context = {
            'documentos_destacados': documentos_destacados,
            'ultimas_gacetas': ultimas_gacetas,
            'carousel_news': carousel_news,
            'chronicles': chronicles,
        }
        return render(request, 'core/home.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar la página principal: {e}')
        # Aún devolvemos la misma plantilla para no romper la navegación
        return render(request, 'core/home.html')





def manage_news_frontend(request):
    """
    [PUNTO DE INTEGRACIÓN DE ROLES]: 
    Validar aquí que el usuario pertenezca al rol de Noticias 
    (que conceptualmente también puede administrar crónicas si se requiere).
    """
    # Buenas prácticas: Manejo de formularios por método POST/GET
    if request.method == 'POST':
        form = HomeCarouselNewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Noticia de carrusel creada exitosamente.')
            return redirect('manage_news_frontend')
    else:
        form = HomeCarouselNewsForm()

    news_list = HomeCarouselNews.objects.all()
    context = {
        'form': form,
        'news_list': news_list,
    }
    return render(request, 'core/manage_news.html', context)





def manage_chronicles_frontend(request):
    """
    [PUNTO DE INTEGRACIÓN DE ROLES]: 
    Validar aquí el acceso exclusivo para el rol de Crónicas.
    """
    if request.method == 'POST':
        form = MunicipalChronicleForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Crónica municipal registrada con éxito.')
            return redirect('manage_chronicles_frontend')
    else:
        form = MunicipalChronicleForm()

    chronicles_list = MunicipalChronicle.objects.all()
    context = {
        'form': form,
        'chronicles_list': chronicles_list,
    }
    return render(request, 'templates/core/manage_chronicles.html', context)


def update_news_frontend(request, pk):
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
    news_item = get_object_or_404(HomeCarouselNews, pk=pk)
    if request.method == 'POST':
        news_item.delete()
        messages.success(request, 'Noticia eliminada correctamente.')
        return redirect('core:manage_news_frontend')
    
    return render(request, 'core/delete_news.html', {'news_item': news_item})

def news_detail_frontend(request, pk):
    news_item = get_object_or_404(HomeCarouselNews, pk=pk, is_active=True)
    
    # Buscar noticias de la misma categoría, excluyendo la actual. Si no hay, mostrar recientes.
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
        from django.db import models



def manage_categories_frontend(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría creada exitosamente.")
            return redirect('core:manage_categories_frontend')
    else:
        form = CategoryForm()

    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'core/manage_categories.html', context)

def update_category_frontend(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría actualizada exitosamente.")
            return redirect('core:manage_categories_frontend')
    else:
        form = CategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
    }
    return render(request, 'core/update_category.html', context)

def delete_category_frontend(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Categoría eliminada exitosamente.")
        return redirect('core:manage_categories_frontend')
    
    context = {'category': category}
    return render(request, 'core/delete_category.html', context)



def news_public_list_frontend(request):
    query = request.GET.get('q', '')
    date_query = request.GET.get('date', '')
    category_slug = request.GET.get('category', '')

    # Listamos todas las noticias (activas o inactivas) según el nuevo requerimiento
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