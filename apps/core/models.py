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

from common.models import BaseModel

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