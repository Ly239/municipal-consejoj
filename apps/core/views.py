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
from django.core.paginator import Paginator
from django.contrib import messages                      # <- necesario para mostrar mensajes
from documents.models import Document, Gazette
# Create your views here.
from django.shortcuts import render
from django.contrib import messages
from documents.models import Document, Gazette

def HomeView(request):
    try:
        # Consultas dinámicas para la base de datos
        documentos_destacados = Document.objects.select_related('gazette', 'document_type').order_by('-publication_date')[:2]
        ultimas_gacetas = Gazette.objects.all()[:3]

        context = {
            'documentos_destacados': documentos_destacados,
            'ultimas_gacetas': ultimas_gacetas,
        }
        return render(request, 'core/home.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar la página principal: {e}')
        # Aún devolvemos la misma plantilla para no romper la navegación
        return render(request, 'core/home.html')