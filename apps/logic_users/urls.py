from django.urls import path
from .views import (
    UserLoginView,
    UserRegisterView,
    UserProfileView,
    UserLogoutView,
    UserListView,
    UserUpdateView,
    UserDeleteView,
)

app_name = 'users'

app_name = 'users' 

urlpatterns = [
    # Rutas de autenticación y perfil existentes
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    # Nuevas rutas para la Gestión de Usuarios (Admin-only)[cite: 3]
    path('', UserListView.as_view(), name='user_list'),
    path('<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
]