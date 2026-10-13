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

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ============================================================
    # 1. PORTAL PÚBLICO GENERAL Y DASHBOARD
    # ============================================================
    path('', views.HomeView.as_view(), name='home'),
    path('quienes-somos/', views.AboutUsView.as_view(), name='about_us'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # ============================================================
    # 2. MÓDULO DE NOTICIAS
    # ============================================================
    path('noticias/', views.news_public_list_frontend, name='news_public_list_frontend'),
    path('noticias/<int:pk>/', views.news_detail_frontend, name='news_detail_frontend'),
    path('gestion/noticias/', views.NewsManageView.as_view(), name='manage_news_frontend'),
    path('gestion/noticias/crear/', views.NewsCreateView.as_view(), name='create_news_frontend'),
    path('gestion/noticias/editar/<int:pk>/', views.NewsUpdateView.as_view(), name='update_news_frontend'),
    path('gestion/noticias/eliminar/<int:pk>/', views.NewsDeleteView.as_view(), name='delete_news_frontend'),

    # ============================================================
    # 3. MÓDULO DE CRÓNICAS MUNICIPALES
    # ============================================================
    path('cronicas/', views.ChronicleListView.as_view(), name='chronicle_public_list'),
    path('cronicas/<slug:slug>/', views.ChronicleDetailView.as_view(), name='chronicle_detail'),
    path('gestion/cronicas/', views.ChronicleManageView.as_view(), name='manage_chronicles'),
    path('gestion/cronicas/crear/', views.ChronicleCreateView.as_view(), name='create_chronicle'),
    path('gestion/cronicas/editar/<int:pk>/', views.ChronicleUpdateView.as_view(), name='edit_chronicle'),
    path('gestion/cronicas/eliminar/<int:pk>/', views.ChronicleDeleteView.as_view(), name='delete_chronicle'),

    # ============================================================
    # 4. MÓDULO DE CATEGORÍAS
    # ============================================================
    path('gestion/categorias/', views.CategoryManageView.as_view(), name='manage_categories_frontend'),
    path('gestion/categorias/crear/', views.CategoryCreateView.as_view(), name='create_category_frontend'),
    path('gestion/categorias/editar/<int:pk>/', views.CategoryUpdateView.as_view(), name='update_category_frontend'),
    path('gestion/categorias/eliminar/<int:pk>/', views.CategoryDeleteView.as_view(), name='delete_category_frontend'),

    # ============================================================
    # 5. MÓDULO DE COMISIONES PERMANENTES
    # ============================================================
    path('comisiones/', views.CommissionsView.as_view(), name='commissions'),
    path('gestion/comisiones/', views.CommissionAdminListView.as_view(), name='commission_admin_list'),
    path('gestion/comisiones/crear/', views.CommissionCreateView.as_view(), name='commission_create'),
    path('gestion/comisiones/editar/<int:pk>/', views.CommissionUpdateView.as_view(), name='commission_update'),
    path('gestion/comisiones/eliminar/<int:pk>/', views.CommissionDeleteView.as_view(), name='commission_delete'),

    # ============================================================
    # 6. MÓDULO DE CONCEJALES Y DIRECTIVA
    # ============================================================
    path('concejales/', views.CouncilorListView.as_view(), name='councilor_list'),
    path('concejales/<slug:slug>/', views.CouncilorDetailView.as_view(), name='councilor_detail'),
    path('gestion/concejales/crear/', views.CouncilorCreateView.as_view(), name='councilor_create'),
    path('gestion/concejales/editar/<int:pk>/', views.CouncilorUpdateView.as_view(), name='councilor_update'),
    path('gestion/concejales/eliminar/<int:pk>/', views.CouncilorDeleteView.as_view(), name='councilor_delete'),

    # ============================================================
    # 7. MÓDULO DE LEGISLATURAS HISTÓRICAS
    # ============================================================
    path('legislaturas/', views.LegislatureListView.as_view(), name='legislature_list'),
    path('gestion/legislaturas/crear/', views.LegislatureCreateView.as_view(), name='legislature_create'),
    path('gestion/legislaturas/editar/<int:pk>/', views.LegislatureUpdateView.as_view(), name='legislature_update'),
    path('gestion/legislaturas/eliminar/<int:pk>/', views.LegislatureDeleteView.as_view(), name='legislature_delete'),

    # ============================================================
    # 8. MÓDULO DE ACTIVIDADES (Públicas y Gestión CRUD)
    # ============================================================
    path('actividades/', views.ActivityListView.as_view(), name='activity_list'),
    path('actividades/<int:pk>/', views.ActivityDetailView.as_view(), name='activity_detail'),
    path('gestion/actividades/', views.ActivityManageView.as_view(), name='manage_activities'),
    path('gestion/actividades/crear/', views.ActivityCreateView.as_view(), name='activity_create'),
    path('gestion/actividades/editar/<int:pk>/', views.ActivityUpdateView.as_view(), name='activity_update'),
    path('gestion/actividades/eliminar/<int:pk>/', views.ActivityDeleteView.as_view(), name='activity_delete'),

    # ============================================================
    # 9. MÓDULO DE LICITACIONES Y ANUNCIOS (Públicas y Gestión CRUD)
    # ============================================================
    path('licitaciones/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('licitaciones/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('gestion/licitaciones/', views.AnnouncementManageView.as_view(), name='manage_announcements'),
    path('gestion/licitaciones/crear/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('gestion/licitaciones/editar/<int:pk>/', views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path('gestion/licitaciones/eliminar/<int:pk>/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),

    # ============================================================
    # 10. MÓDULO DE CONSULTAS PÚBLICAS (Públicas y Gestión CRUD)
    # ============================================================
    path('consultas-publicas/', views.ConsultationListView.as_view(), name='consultation_list'),
    path('consultas-publicas/<int:pk>/', views.ConsultationDetailView.as_view(), name='consultation_detail'),
    path('gestion/consultas-publicas/', views.ConsultationManageView.as_view(), name='manage_consultations'),
    path('gestion/consultas/crear/', views.ConsultationCreateView.as_view(), name='consultation_create'),
    path('gestion/consultas/editar/<int:pk>/', views.ConsultationUpdateView.as_view(), name='consultation_update'),
    path('gestion/consultas/eliminar/<int:pk>/', views.ConsultationDeleteView.as_view(), name='consultation_delete'),

    # ============================================================
    # 11. MÓDULO DE EVENTOS INSTITUCIONALES (Públicas y Gestión CRUD)
    # ============================================================
    path('eventos/', views.EventListView.as_view(), name='event_list'),
    path('eventos/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('gestion/eventos/', views.EventManageView.as_view(), name='manage_events'),
    path('gestion/eventos/crear/', views.EventCreateView.as_view(), name='event_create'),
    path('gestion/eventos/editar/<int:pk>/', views.EventUpdateView.as_view(), name='event_update'),
    path('gestion/eventos/eliminar/<int:pk>/', views.EventDeleteView.as_view(), name='event_delete'),

    # ============================================================
    # 12. MÓDULO DE DOCUMENTOS DESCARGABLES (Públicas y Gestión CRUD)
    # ============================================================
    path('descargables/', views.DownloadableListView.as_view(), name='downloadable_list'),
    path('gestion/descargables/', views.DownloadableManageView.as_view(), name='manage_downloadables'),
    path('gestion/descargables/crear/', views.DownloadableCreateView.as_view(), name='downloadable_create'),
    path('gestion/descargables/editar/<int:pk>/', views.DownloadableUpdateView.as_view(), name='downloadable_update'),
    path('gestion/descargables/eliminar/<int:pk>/', views.DownloadableDeleteView.as_view(), name='delete_downloadable'),

    # ============================================================
    # 13. MÓDULO INSTITUCIONAL (GESTIÓN SOBRE NOSOTROS)
    # ============================================================
    path('gestion/quienes-somos/', views.AboutUsManageView.as_view(), name='manage_about_us'),
    path('gestion/quienes-somos/editar/', views.AboutUsUpdateView.as_view(), name='about_us_update'),
]