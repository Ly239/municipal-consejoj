from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin #Para autenticacion de usuario
from django.contrib.auth import authenticate,login, get_user_model,logout
from django.views import View
from django.core.paginator import Paginator
from django.contrib import messages                      # <- necesario para mostrar mensajes

# Create your views here.

def HomeView(request):
    try:
        return render(request, 'core/home.html')
    except Exception as e:
        messages.error(request, f'Error al cargar la página principal: {e}')
        # Aún devolvemos la misma plantilla para no romper la navegación
        return render(request, 'core/home.html')