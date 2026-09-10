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
from django.utils.text import slugify
from common.models import BaseModel

# MODELOS NORMALES FALTA ACTUALIZARLOS A PROXY MODELS
class Category(models.Model):
    """Categorías para clasificar noticias y documentos del portal."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class HomeCarouselNews(models.Model):
    """Noticias destacadas que se muestran en el carrusel de la página principal."""
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


class Chronicle(models.Model):
    """Modelo unificado para gestionar las crónicas e historia local del municipio."""
    title = models.CharField(max_length=200, verbose_name="Título de la Crónica")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="Slug")
    summary = models.TextField(verbose_name="Resumen o Bajada")
    content = models.TextField(verbose_name="Contenido Completo")
    image = models.ImageField(upload_to='chronicles_img/', blank=True, null=True, verbose_name="Imagen Destacada")
    author = models.CharField(max_length=150, default="Cronista Oficial", verbose_name="Autor / Cronista")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    is_active = models.BooleanField(default=True, verbose_name="¿Publicado?")

    class Meta:
        verbose_name = "Crónica"
        verbose_name_plural = "Crónicas"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Genera automáticamente un slug único basado en el título antes de guardar."""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Chronicle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


#NOTA ACTUALIZAR CAMPOS A INGLES
class EstructuraDirectiva(models.Model):
  cargo = models.CharField(
      max_length=150, verbose_name='Cargo Institucional'
  )
  nombre = models.CharField(max_length=150, verbose_name='Nombre del Titular')
  descripcion = models.TextField(verbose_name='Descripción o Funciones')
  imagen = models.ImageField(
      upload_to='estructura_directiva/',
      blank=True,
      null=True,
      verbose_name='Fotografía',
  )
  orden = models.PositiveIntegerField(
      default=0, verbose_name='Orden de Visualización'
  )

  class Meta:
    verbose_name = 'Estructura Directiva'
    verbose_name_plural = 'Estructura Directiva'
    ordering = ['orden']

  def __str__(self):
    return f'{self.cargo} - {self.nombre}'

#NOTA ACTUALIZAR CAMPOS A INGLES
class Legislatura(models.Model):
  titulo = models.CharField(
      max_length=100, verbose_name='Título (Ej. I Legislatura)'
  )
  periodo = models.CharField(
      max_length=50, verbose_name='Período (Ej. 1992 - 1995)'
  )
  descripcion_concejales = models.TextField(
      verbose_name='Concejales Integrantes / Datos'
  )
  es_actual = models.BooleanField(
      default=False, verbose_name='¿Es la legislatura actual?'
  )
  orden = models.PositiveIntegerField(
      default=0, verbose_name='Orden de Aparición'
  )

  class Meta:
    verbose_name = 'Legislatura'
    verbose_name_plural = 'Legislaturas'
    ordering = ['orden']

  def __str__(self):
    return f'{self.titulo} ({self.periodo})'


# ============================================================
# 1. PHYSICAL SINGLE TABLE (Home Content)
# ============================================================
class HomeContent(BaseModel):
    """Tabla única que almacena todo el contenido editable del Home."""
    
    class ContentTypes(models.TextChoices):
        COUNCILOR = 'COUNCILOR', 'Councilor'
        NEWS = 'NEWS', 'News'
        CAROUSEL = 'CAROUSEL', 'Carousel'
        ABOUT_US = 'ABOUT_US', 'About Us'

    content_type = models.CharField(max_length=20, choices=ContentTypes.choices)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='home/%Y/%m/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    publication_date = models.DateTimeField(auto_now_add=True, verbose_name="Publication Date")

    class Meta:
        ordering = ['content_type', 'order']
        verbose_name = "Home Content"
        verbose_name_plural = "Home Contents"

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title[:30]}"


# ============================================================
# 2. PROXY MODELS (Modelos Fantasma)
# ============================================================

# Councilor (Concejal)
class CouncilorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type=HomeContent.ContentTypes.COUNCILOR, is_active=True)

class Councilor(HomeContent):
    objects = CouncilorManager()

    class Meta:
        proxy = True
        verbose_name = "Councilor"
        verbose_name_plural = "Councilors"

    @property
    def full_name(self):
        return self.title

    @property
    def position(self):
        return self.description


# News (Noticia)
class NewsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type=HomeContent.ContentTypes.NEWS, is_active=True)

class News(HomeContent):
    objects = NewsManager()

    class Meta:
        proxy = True
        verbose_name = "News"
        verbose_name_plural = "News"

    @property
    def date(self):
        return self.publication_date


# Carousel (Carrusel)
# NOTA: Este modelo NO se usa actualmente para el carrusel.
# El carrusel toma las 3 noticias más recientes del proxy News.
# Se mantiene por si en el futuro se necesita un carrusel personalizado.
class CarouselManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type=HomeContent.ContentTypes.CAROUSEL, is_active=True)

class Carousel(HomeContent):
    objects = CarouselManager()

    class Meta:
        proxy = True
        verbose_name = "Carousel"
        verbose_name_plural = "Carousel"

    @property
    def image_url(self):
        return self.image.url if self.image else None


# About Us (Sobre Nosotros)
class AboutUsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(content_type=HomeContent.ContentTypes.ABOUT_US, is_active=True)

class AboutUs(HomeContent):
    objects = AboutUsManager()

    class Meta:
        proxy = True
        verbose_name = "About Us"
        verbose_name_plural = "About Us"

    @property
    def content(self):
        return self.description

