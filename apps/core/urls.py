# core/urls.py
from django.urls import path
from .views import HomeView, manage_news_frontend, manage_chronicles_frontend, delete_news_frontend, update_news_frontend, news_detail_frontend, manage_categories_frontend, update_category_frontend, delete_category_frontend, news_public_list_frontend

app_name= 'core'

urlpatterns = [
    path('', HomeView, name='home'),
    path('dashboard/', HomeView, name='dashboard'),
    path('noticias/<int:pk>/', news_detail_frontend, name='news_detail_frontend'),
    path('gestion/noticias/', manage_news_frontend, name='manage_news_frontend'),
    path('gestion/cronicas/', manage_chronicles_frontend, name='manage_chronicles_frontend'),
    path('gestion/noticias/editar/<int:pk>/', update_news_frontend, name='update_news_frontend'),
    path('gestion/noticias/eliminar/<int:pk>/', delete_news_frontend, name='delete_news_frontend'),
    path('gestion/categorias/', manage_categories_frontend, name='manage_categories_frontend'),
    path('gestion/categorias/editar/<int:pk>/', update_category_frontend, name='update_category_frontend'),
    path('gestion/categorias/eliminar/<int:pk>/', delete_category_frontend, name='delete_category_frontend'),
    path('noticias/', news_public_list_frontend, name='news_public_list_frontend'),

]
#path('dashboard/', DashboardView.as_view(), name='dashboard'),