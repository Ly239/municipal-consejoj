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
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings

# Asumiendo que BaseModel está definido en tu proyecto



# ==============================================================================
# 0. CLASE BASE ABSTRACTA REDUNDANTE YA EXISTE EN COMMON
# ==============================================================================
#ESTO GENERA UN CONFLICTO PORQUE YA EXISTE UNA MODELS CON ESTE NOMBRE
class BaseModel(models.Model):
    """ELIMINAR."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        abstract = True


# ==============================================================================
# 1. TABLA BASE FÍSICA ÚNICA (SINGLE TABLE DESIGN)
# ==============================================================================
  # Ajusta la importación según donde esté tu BaseModel


class HomeContent(BaseModel):
    """Tabla física centralizada para la gestión de contenidos dinámicos del portal."""

    class ContentTypes(models.TextChoices):
        NEWS = 'NEWS', 'Noticia'
        CHRONICLE = 'CHRONICLE', 'Crónica Digital'
        CAROUSEL = 'CAROUSEL', 'Item de Carrusel'
        ABOUT_US = 'ABOUT_US', 'Información Institucional'
        COUNCILOR = 'COUNCILOR', 'Concejal / Directivo'
        LEGISLATURE = 'LEGISLATURE', 'Legislatura / Período'
        BOARD = 'BOARD', 'Junta Directiva'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        PUBLISHED = 'PUBLISHED', 'Publicado'
        ARCHIVED = 'ARCHIVED', 'Archivado'

    # Discriminador principal
    content_type = models.CharField(
        max_length=20, 
        choices=ContentTypes.choices, 
        default=ContentTypes.NEWS,
        verbose_name="Tipo de Contenido"
    )

    # Campos generales
    title = models.CharField(max_length=255, verbose_name="Título / Nombre Completo")
    slug = models.SlugField(max_length=255, blank=True)
    author = models.CharField(max_length=150, default="Concejo Municipal", verbose_name="Autor / Cargo o Partido")
    summary = models.TextField(blank=True, verbose_name="Resumen / Bajada / Biografía Corta")
    content = models.TextField(blank=True, verbose_name="Contenido Extenso / Trayectoria")
    description = models.TextField(blank=True, verbose_name="Descripción Corta (Compatibilidad)")

    # Archivos multimedia, documentos y enlaces
    image = models.ImageField(upload_to='home/%Y/%m/', blank=True, null=True, verbose_name="Imagen / Foto Oficial")
    attached_file = models.FileField(upload_to='home/docs/%Y/%m/', blank=True, null=True, verbose_name="Archivo Adjunto General")
    
    # Campos de soporte para Gacetas / Documentos PDF
    pdf_file = models.FileField(
        upload_to='news_pdfs/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Documento PDF Adjunto",
        help_text="Cargue aquí la Gaceta Oficial, Ordenanza o documento en PDF respaldatorio."
    )
    show_pdf_inline = models.BooleanField(
        default=False,
        verbose_name="Mostrar visor de PDF incrustado",
        help_text="Si está marcado, el PDF se mostrará incrustado directamente en la vista."
    )
    social_media_url = models.URLField(blank=True, null=True, verbose_name="Enlace de Red Social / Web")

    # Control de publicación, orden y visibilidad
    publication_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PUBLISHED, verbose_name="Estado")
    is_active = models.BooleanField(default=True, verbose_name="¿Activo?")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden de Aparición")

    # Relaciones
    category = models.ForeignKey(
        'Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='contents',
        verbose_name="Categoría"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_home_contents',
        verbose_name="Registrado por"
    )

    class Meta:
        ordering = ['content_type', 'order', '-publication_date']
        verbose_name = "Contenido del Home"
        verbose_name_plural = "Contenidos del Home"

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while HomeContent.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if not self.description and self.summary:
            self.description = self.summary
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_content_type_display()}] {self.title}"

    @property
    def full_name(self):
        return self.title

    @property
    def position(self):
        return self.author

    @property
    def date(self):
        return self.publication_date

    @property
    def bio(self):
        return self.summary



# Alias de compatibilidad por si en algún módulo se importa BaseContent
BaseContent = HomeContent


# ==============================================================================
# 2. GESTORES PERSONALIZADOS (CUSTOM MANAGERS)
# ==============================================================================

class ContentManager(models.Manager):
    def __init__(self, content_type, *args, **kwargs):
        self.target_type = content_type
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(content_type=self.target_type, is_active=True)


# ==============================================================================
# 3. PROXY MODELS (MODELOS FANTASMA)
# ==============================================================================

class News(HomeContent):
    objects = ContentManager(HomeContent.ContentTypes.NEWS)

    class Meta:
        proxy = True
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"

    def save(self, *args, **kwargs):
        self.content_type = HomeContent.ContentTypes.NEWS
        super().save(*args, **kwargs)


class Chronicle(HomeContent):
    objects = ContentManager(HomeContent.ContentTypes.CHRONICLE)

    class Meta:
        proxy = True
        verbose_name = "Crónica Digital"
        verbose_name_plural = "Crónicas Digitales"

    def save(self, *args, **kwargs):
        self.content_type = HomeContent.ContentTypes.CHRONICLE
        super().save(*args, **kwargs)


class Councilor(HomeContent):
    objects = ContentManager(HomeContent.ContentTypes.COUNCILOR)

    class Meta:
        proxy = True
        verbose_name = "Concejal / Directivo"
        verbose_name_plural = "Concejales y Directiva"

    def save(self, *args, **kwargs):
        self.content_type = HomeContent.ContentTypes.COUNCILOR
        super().save(*args, **kwargs)


class Carousel(HomeContent):
    objects = ContentManager(HomeContent.ContentTypes.CAROUSEL)

    class Meta:
        proxy = True
        verbose_name = "Item de Carrusel"
        verbose_name_plural = "Items del Carrusel"

    def save(self, *args, **kwargs):
        self.content_type = HomeContent.ContentTypes.CAROUSEL
        super().save(*args, **kwargs)


class AboutUs(HomeContent):
    objects = ContentManager(HomeContent.ContentTypes.ABOUT_US)

    class Meta:
        proxy = True
        verbose_name = "Información Institucional"
        verbose_name_plural = "Información Institucional"

    def save(self, *args, **kwargs):
        self.content_type = HomeContent.ContentTypes.ABOUT_US
        super().save(*args, **kwargs)


class Legislature(HomeContent):
    """Proxy Model para la gestión de Legislaturas / Períodos Legislativos."""
    class Meta:
        proxy = True
        verbose_name = 'Legislatura'
        verbose_name_plural = 'Legislaturas'


class BoardMember(HomeContent):
    """Proxy Model para la gestión de Integrantes de la Junta Directiva."""
    class Meta:
        proxy = True
        verbose_name = 'Junta Directiva'
        verbose_name_plural = 'Junta Directiva'

# ==============================================================================
# 4. ESTRUCTURAS AUXILIARES Y LEGISLATIVAS
# ==============================================================================

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Commission(models.Model):
    """Modelo para las 15 Comisiones Permanentes de Trabajo del Concejo Municipal."""
    number = models.PositiveIntegerField(unique=True, verbose_name="Número de Comisión")
    name = models.CharField(max_length=250, verbose_name="Nombre de la Comisión")
    description = models.TextField(blank=True, verbose_name="Área de Trabajo / Funciones")
    image = models.ImageField(
        upload_to='commissions/%Y/%m/', 
        blank=True, 
        null=True, 
        verbose_name="Imagen / Foto de la Comisión"
    )

    # Vinculación directa con los concejales registrados en HomeContent
    president = models.ForeignKey(
        HomeContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'content_type': HomeContent.ContentTypes.COUNCILOR},
        related_name='commissions_as_president',
        verbose_name="Presidente de la Comisión"
    )
    vice_president = models.ForeignKey(
        HomeContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'content_type': HomeContent.ContentTypes.COUNCILOR},
        related_name='commissions_as_vicepresident',
        verbose_name="Vicepresidente de la Comisión"
    )
    vocal = models.ForeignKey(
        HomeContent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'content_type': HomeContent.ContentTypes.COUNCILOR},
        related_name='commissions_as_vocal',
        verbose_name="Vocal de la Comisión"
    )

    class Meta:
        ordering = ['number']
        verbose_name = "Comisión Permanente"
        verbose_name_plural = "Comisiones Permanentes"

    def __str__(self):
        return f"Comisión N° {self.number}: {self.name}"

    @property
    def emoji(self):
        """Mapeo dinámico de emojis para las 15 comisiones permanentes."""
        emojis = {
            1: '⚖️',   # Derechos Humanos, Justicia y Familia
            2: '⚽',   # Deporte y Juventud
            3: '🎓',   # Educación y Cultura
            4: '🏛️',   # Historia, Patrimonio y Turismo
            5: '📐',   # Ejidos
            6: '💰',   # Presupuesto
            7: '🔍',   # Contraloría
            8: '🤝',   # Participación Ciudadana, Política y Frontera
            9: '📜',   # Legislación
            10: '🏗️',  # Obras Públicas y Ordenamiento del Territorio
            11: '🚰',  # Servicios Públicos
            12: '🚌',  # Transporte
            13: '🏥',  # Salud, Ambiente y Actividades Agrícolas
            14: '📡',  # Comunicación Social y Tecnología
            15: '🎉',  # Eventos Públicos
        }
        return emojis.get(self.number, '📋')




