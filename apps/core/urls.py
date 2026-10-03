# core/urls.py
from django.urls import path
from .views import (
    HomeView,
    DashboardView,
    news_public_list_frontend,
    news_detail_frontend,
    chronicle_public_list,
    chronicle_detail,
    manage_news_frontend,
    update_news_frontend,
    delete_news_frontend,
    manage_categories_frontend,
    update_category_frontend,
    delete_category_frontend,
    manage_chronicles,
    save_chronicle,
    delete_chronicle,
    CommissionAdminListView,
    CommissionCreateView,
    CommissionDeleteView,
    CommissionUpdateView,
    CommissionsView,
    CouncilorListView,
    CouncilorDetailView,
    CouncilorUpdateView,
    CouncilorCreateView,
    CouncilorDeleteView,
)
from . import views

app_name = 'core'


urlpatterns = [
    # 1. Portal Público General
    path('', views.HomeView.as_view(), name='home'),
    path('quienes-somos/', views.AboutUsView.as_view(), name='about_us'),

    # 2. Noticias
    path('noticias/', views.news_public_list_frontend, name='news_public_list_frontend'),
    path('noticias/<int:pk>/', views.news_detail_frontend, name='news_detail_frontend'),
    path('gestion/noticias/', views.manage_news_frontend, name='manage_news_frontend'),
    path('gestion/noticias/editar/<int:pk>/', views.update_news_frontend, name='update_news_frontend'),
    path('gestion/noticias/eliminar/<int:pk>/', views.delete_news_frontend, name='delete_news_frontend'),

    # 3. Crónicas
    path('cronicas/', views.chronicle_public_list, name='chronicle_public_list'),
    path('cronicas/<slug:slug>/', views.chronicle_detail, name='chronicle_detail'),
    path('gestion/cronicas/', views.manage_chronicles, name='manage_chronicles'),
    path('gestion/cronicas/crear/', views.save_chronicle, name='create_chronicle'),
    path('gestion/cronicas/editar/<int:pk>/', views.save_chronicle, name='edit_chronicle'),
    path('gestion/cronicas/eliminar/<int:pk>/', views.delete_chronicle, name='delete_chronicle'),

    # 4. Categorías
    path('gestion/categorias/', views.manage_categories_frontend, name='manage_categories_frontend'),
    path('gestion/categorias/editar/<int:pk>/', views.update_category_frontend, name='update_category_frontend'),
    path('gestion/categorias/eliminar/<int:pk>/', views.delete_category_frontend, name='delete_category_frontend'),

    # 5. Comisiones
    path('comisiones/', views.CommissionsView.as_view(), name='commissions'),
    path('gestion/comisiones/', views.CommissionAdminListView.as_view(), name='commission_admin_list'),
    path('gestion/comisiones/crear/', views.CommissionCreateView.as_view(), name='commission_create'),
    path('gestion/comisiones/editar/<int:pk>/', views.CommissionUpdateView.as_view(), name='commission_update'),
    path('gestion/comisiones/eliminar/<int:pk>/', views.CommissionDeleteView.as_view(), name='commission_delete'),

    # 6. Concejales
    path('concejales/', views.CouncilorListView.as_view(), name='councilors'),
    path('concejales/<slug:slug>/', views.CouncilorDetailView.as_view(), name='councilor_detail'),
    path('gestion/concejales/crear/', views.CouncilorCreateView.as_view(), name='councilor_create'),
    path('gestion/concejales/editar/<int:pk>/', views.CouncilorUpdateView.as_view(), name='councilor_update'),
    path('gestion/concejales/eliminar/<int:pk>/', views.CouncilorDeleteView.as_view(), name='councilor_delete'),

    # 7. Módulo de Legislaturas
    path('legislaturas/', views.LegislatureListView.as_view(), name='legislatures_list'),
    path('gestion/legislaturas/crear/', views.LegislatureCreateView.as_view(), name='legislature_create'),
    path('gestion/legislaturas/editar/<int:pk>/', views.LegislatureUpdateView.as_view(), name='legislature_update'),
    path('gestion/legislaturas/eliminar/<int:pk>/', views.LegislatureDeleteView.as_view(), name='legislature_delete'),


    # 8. Dashboard Administrativo
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]
