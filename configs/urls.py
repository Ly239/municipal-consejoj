"""configs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# URL principal configuration for config project.
from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static # Importa static



urlpatterns = [
	path('', include('core.urls')),
    path('users/', include('logic_users.urls')),  # URLs de login/logout
    path('documents/', include('documents.urls')),
    path('common/', include('common.urls')),
    path('admin/', admin.site.urls),
]


# Al final del archivo, fuera de la lista urlpatterns:
# Vista para la template error404:
def mi_vista_404(request, exception):
    return render(request, 'template404/404.html', status=404)

handler404 = 'configs.urls.mi_vista_404'


# if settings.DEBUG:
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
