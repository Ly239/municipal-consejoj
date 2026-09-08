# core/urls.py
from django.urls import path
from .views import *


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('news/<int:pk>/', NewsDetailView.as_view(), name='news_detail'),
    path('councilors/', CouncilorsView.as_view(), name='councilors'),
    path('commissions/', CommissionsView.as_view(), name='commissions'),
    path('about_us/', AboutUsView.as_view(), name='about_us'),


]
