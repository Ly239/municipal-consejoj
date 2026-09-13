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
    CouncilorsView,
    CommissionsView,
    AboutUsView,
    NewsDetailView,
)



app_name = 'core'


urlpatterns = [

    # Rutas Principales y Dashboard
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('news/<int:pk>/', NewsDetailView.as_view(), name='news_detail'),
    path('councilors/', CouncilorsView.as_view(), name='councilors'),
    path('commissions/', CommissionsView.as_view(), name='commissions'),
    path('about_us/', AboutUsView.as_view(), name='about_us'),
    
    # Rutas Públicas (Noticias y Crónicas)
    path('noticias/', news_public_list_frontend, name='news_public_list_frontend'),
    path('noticias/<int:pk>/', news_detail_frontend, name='news_detail_frontend'),
    path('cronicas/', chronicle_public_list, name='chronicle_public_list'),
    path('cronica/<slug:slug>/', chronicle_detail, name='chronicle_detail'),
    
    # Gestión de Noticias (Backend / Panel)
    path('gestion/noticias/', manage_news_frontend, name='manage_news_frontend'),
    path('gestion/noticias/editar/<int:pk>/', update_news_frontend, name='update_news_frontend'),
    path('gestion/noticias/eliminar/<int:pk>/', delete_news_frontend, name='delete_news_frontend'),
    
    # Gestión de Categorías
    path('gestion/categorias/', manage_categories_frontend, name='manage_categories_frontend'),
    path('gestion/categorias/editar/<int:pk>/', update_category_frontend, name='update_category_frontend'),
    path('gestion/categorias/eliminar/<int:pk>/', delete_category_frontend, name='delete_category_frontend'),
    
    # Gestión de Crónicas
    path('gestion/cronicas/', manage_chronicles, name='manage_chronicles'),
    path('gestion/cronicas/nueva/', save_chronicle, name='create_chronicle'),
    path('gestion/cronicas/editar/<int:pk>/', save_chronicle, name='edit_chronicle'),
    path('gestion/cronicas/eliminar/<int:pk>/', delete_chronicle, name='delete_chronicle'),
]