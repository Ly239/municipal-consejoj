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
from django.db import models



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class HomeCarouselNews(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título")
    summary = models.TextField(verbose_name="Resumen / Tráiler")
    content = models.TextField(verbose_name="Contenido Completo", blank=True, null=True, help_text="Texto completo para la vista de detalle")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoría")
    image = models.ImageField(upload_to='news/', verbose_name="Imagen")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    is_active = models.BooleanField(default=True, verbose_name="Activo en Portada")
    created_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='news_pdfs/', blank=True, null=True, verbose_name="Documento PDF de Respaldo")
    show_pdf_inline = models.BooleanField(default=False, verbose_name="¿Mostrar PDF en visor interactivo?")
    social_media_url = models.URLField(blank=True, null=True, verbose_name="Enlace de Red Social (Instagram, Facebook, TikTok)")
    def __str__(self):
        return self.title


class MunicipalChronicle(models.Model):
    """Modelo para gestionar la sección de crónicas municipales."""
    title = models.CharField(max_length=200, verbose_name="Título de la Crónica")
    content = models.TextField(verbose_name="Contenido")
    image = models.ImageField(upload_to='home/chronicles/', blank=True, null=True, verbose_name="Imagen ilustrativa")
    publication_date = models.DateField(verbose_name="Fecha de publicación")
    is_published = models.BooleanField(default=True, verbose_name="Publicado")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Crónica Municipal"
        verbose_name_plural = "Crónicas Municipales"
        ordering = ['-publication_date']

    def __str__(self):
        return self.title
