"""
Modelos de la app core del Concejo Municipal de Junín.

Contiene:
- BaseContent: tabla única de contenido dinámico del Home.
- Proxies de contenido: News, Chronicle, Councilor, AboutUs.
- Proxies de actividades: Activity (paraguas), Announcement, Consultation, Event, Downloadable.
- Auxiliares: Category, Commission, Legislature, Legislator.

Arquitectura:
- Todo el contenido editorial vive en BaseContent (una sola tabla real).
- Los proxies NO crean tablas; solo filtran por content_type y subtype.
- Los auxiliares (Category, Commission, Legislature, Legislator) son relaciones
  entre entidades, no contenido; por eso viven en tablas separadas.

Soft delete:
- Core NO usa soft delete. Elimina permanente (hard delete).
- Por eso hereda solo de common.TimestampedMixin (no de common.BaseModel).
- Como consecuencia, NO aparece en la papelera universal (no es subclase
  de SoftDeleteMixin, por lo que common.apps.ready() lo ignora).
- El delete() está sobrescrito para limpiar archivos físicos antes de borrar.
- Principio espejo: common.SoftDeleteMixin.hard_delete() hace lo mismo en su capa.
"""
import logging

from django.db import models, IntegrityError
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings

from common.models import TimestampedMixin

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. GESTORES PERSONALIZADOS (Custom Managers)
# ==============================================================================

class ContentManager(models.Manager):
    """
    Manager que filtra por content_type.
    Se usa en los proxies de contenido (News, Chronicle, Councilor, AboutUs).
    No filtra por deleted_at porque core no usa soft delete.
    """
    use_in_migrations = False

    def __init__(self, *args, content_type=None, **kwargs):
        self.target_type = content_type
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.target_type:
            qs = qs.filter(content_type=self.target_type)
        return qs


class ActivityManager(models.Manager):
    """
    Manager para los 4 subtipos de Activity.
    Filtra por content_type=ACTIVITY + subtype específico.
    """
    use_in_migrations = False

    def __init__(self, *args, subtype=None, **kwargs):
        self.target_subtype = subtype
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset().filter(
            content_type=BaseContent.ContentType.ACTIVITY,
        )
        if self.target_subtype:
            qs = qs.filter(subtype=self.target_subtype)
        return qs


# ==============================================================================
# 2. TABLA ÚNICA DE CONTENIDO (BaseContent)
# ==============================================================================

class BaseContent(TimestampedMixin, models.Model):
    """
    Tabla única que almacena TODO el contenido editorial del Home.

    Discriminadores:
    - content_type: define el tipo (News, Chronicle, Councilor, AboutUs, Activity).
    - subtype: solo aplica a Activity (Announcement, Consultation, Event, Downloadable).

    Hereda de TimestampedMixin (created_at, updated_at) — NO de common.BaseModel,
    porque core no usa soft delete.
    """

    class ContentType(models.TextChoices):
        NEWS = 'NEWS', 'Noticia'
        CHRONICLE = 'CHRONICLE', 'Crónica Digital'
        ABOUT_US = 'ABOUT_US', 'Información Institucional'
        COUNCILOR = 'COUNCILOR', 'Concejal / Directivo'
        ACTIVITY = 'ACTIVITY', 'Actividad / Difusión'

    class ActivitySubtype(models.TextChoices):
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Llamado a Concurso'
        CONSULTATION = 'CONSULTATION', 'Consulta Pública'
        EVENT = 'EVENT', 'Evento / Difusión'
        DOWNLOADABLE = 'DOWNLOADABLE', 'Descargable'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        PUBLISHED = 'PUBLISHED', 'Publicado'
        ARCHIVED = 'ARCHIVED', 'Archivado'

    # --- Discriminadores ---
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
        default=ContentType.NEWS,
        verbose_name="Tipo de Contenido"
    )
    subtype = models.CharField(
        max_length=20,
        choices=ActivitySubtype.choices,
        blank=True,
        verbose_name="Subtipo (solo Actividades)"
    )

    # --- Identificación ---
    title = models.CharField(max_length=255, verbose_name="Título / Nombre Completo")
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name="Slug (URL)"
    )
    author = models.CharField(
        max_length=150,
        default="Concejo Municipal",
        verbose_name="Autor / Cargo"
    )

    # --- Contenido ---
    summary = models.TextField(blank=True, verbose_name="Resumen / Biografía Corta")
    content = models.TextField(blank=True, verbose_name="Contenido Extenso")

    # --- Multimedia ---
    image = models.ImageField(
        upload_to='contents/images/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Imagen / Foto"
    )
    attached_file = models.FileField(
        upload_to='contents/docs/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Archivo Adjunto (PDF)"
    )
    show_pdf_inline = models.BooleanField(
        default=False,
        verbose_name="Mostrar visor de PDF incrustado",
        help_text="Si está marcado, el PDF adjunto se mostrará embebido en la vista de detalle."
    )
    social_media_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Enlace de Red Social / Web"
    )

    # --- Estado y visibilidad ---
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PUBLISHED,
        verbose_name="Estado"
    )
    is_active = models.BooleanField(default=True, verbose_name="¿Activo?")
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Destacar en 'Lo Último'"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    # --- Campos específicos de Activity (inline, solo aplican a los 4 subtipos) ---
    code = models.CharField(max_length=100, blank=True, verbose_name="Código (Licitaciones)")
    law_reference = models.TextField(blank=True, verbose_name="Base Legal")
    contact_email = models.EmailField(blank=True, verbose_name="Correo de Contacto")
    start_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Inicio")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Culminación")
    year = models.CharField(max_length=4, blank=True, verbose_name="Año (Descargables)")

    # --- Relaciones ---
    # PROTECT: no se puede borrar una categoría o un usuario con contenido asociado.
    category = models.ForeignKey(
        'Category',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='contents',
        verbose_name="Categoría"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_contents',
        verbose_name="Registrado por"
    )

    class Meta:
        # ordering usa created_at (campo real) — publication_date es property.
        ordering = ['order', '-created_at']
        verbose_name = "Contenido del Home"
        verbose_name_plural = "Contenidos del Home"
        indexes = [
            models.Index(fields=['content_type', 'is_active']),
            models.Index(fields=['subtype', 'is_active']),
        ]
        # (parcial): permisos custom de core.
        # Django ya crea add/change/delete/view automáticamente.
        # can_edit_home se asigna al grupo contentmanager y Administrator en seed_roles.py.
        permissions = [
            ('can_edit_home', 'Can edit home content'),
        ]

    def save(self, *args, **kwargs):
        """
        Genera slug único a partir del título si no existe.

        Estrategia de unicidad:
        - Loop en Python para cubrir el 99% de los casos (colisiones normales).
        - unique=True a nivel BD como red de seguridad (concurrencia real).
        - Si por carrera concurrente se produce IntegrityError, se reintenta
          UNA vez con el slug regenerado.
        """
        if not self.slug and self.title:
            self.slug = self._build_unique_slug()
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            if self.slug and self.title:
                # Colisión por concurrencia: regenerar y reintentar una vez.
                self.slug = self._build_unique_slug()
                super().save(*args, **kwargs)
            else:
                raise

    def _build_unique_slug(self):
        """Construye un slug único con contador sufijo (-1, -2, ...)."""
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while BaseContent.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def clean(self):
        """Validaciones de consistencia entre content_type y subtype."""
        from django.core.exceptions import ValidationError

        # Solo ACTIVITY puede tener subtype
        if self.content_type != self.ContentType.ACTIVITY and self.subtype:
            raise ValidationError({
                'subtype': 'Solo las Actividades pueden tener subtipo.'
            })

        # Rango de fechas en actividades con inicio/fin
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': 'La fecha de culminación no puede ser anterior a la de inicio.'
            })

    def delete(self, *args, **kwargs):
        """
        Borrado permanente.

        Limpia archivos físicos (image, attached_file) antes de borrar la fila.
        Django por defecto NO elimina archivos del storage al borrar el objeto;
        este override evita dejar archivos huérfanos ocupando disco.
        """
        for field in self._meta.get_fields():
            if isinstance(field, (models.FileField, models.ImageField)):
                file = getattr(self, field.name, None)
                if file and file.name:
                    file.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_content_type_display()}] {self.title[:50]}"

    # --- Propiedades de compatibilidad con templates existentes ---
    @property
    def description(self):
        """Alias de summary. Reemplaza al campo description duplicado."""
        return self.summary

    @property
    def publication_date(self):
        """Alias semántico de created_at. No es campo, no duplica en BD."""
        return self.created_at

    @property
    def date(self):
        """Alias de publication_date (compatibilidad con templates)."""
        return self.created_at

    @property
    def name(self):
        """Alias de title (compatibilidad con templates)."""
        return self.title

    @property
    def position(self):
        """Alias de author (compatibilidad con templates)."""
        return self.author

    @property
    def bio(self):
        """Alias de summary (compatibilidad con templates)."""
        return self.summary

    @property
    def full_name(self):
        """Alias de title (compatibilidad con código previo de Fersan)."""
        return self.title


# ==============================================================================
# 3. PROXIES DE CONTENIDO (News, Chronicle, Councilor, AboutUs)
# ==============================================================================

class News(BaseContent):
    """Proxy para Noticias."""
    objects = ContentManager(content_type=BaseContent.ContentType.NEWS)

    class Meta:
        proxy = True
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.NEWS
        super().save(*args, **kwargs)


class Chronicle(BaseContent):
    """Proxy para Crónicas Digitales."""
    objects = ContentManager(content_type=BaseContent.ContentType.CHRONICLE)

    class Meta:
        proxy = True
        verbose_name = "Crónica Digital"
        verbose_name_plural = "Crónicas Digitales"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.CHRONICLE
        super().save(*args, **kwargs)


class Councilor(BaseContent):
    """Proxy para Concejales y Directiva."""
    objects = ContentManager(content_type=BaseContent.ContentType.COUNCILOR)

    class Meta:
        proxy = True
        verbose_name = "Concejal / Directivo"
        verbose_name_plural = "Concejales y Directiva"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.COUNCILOR
        super().save(*args, **kwargs)


class AboutUs(BaseContent):
    """
    Proxy para Información Institucional.
    Cada sección (Quiénes somos, Misión, Visión) es un registro
    identificado por su slug: 'quienes-somos', 'mision', 'vision'.
    """
    objects = ContentManager(content_type=BaseContent.ContentType.ABOUT_US)

    class Meta:
        proxy = True
        verbose_name = "Información Institucional"
        verbose_name_plural = "Información Institucional"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.ABOUT_US
        super().save(*args, **kwargs)


# ==============================================================================
# 4. ACTIVITY (paraguas) + 4 SUBTIPOS
# ==============================================================================

class Activity(BaseContent):
    """
    Proxy 'paraguas' para TODAS las actividades (cualquier subtipo).

    Uso: consultas cronológicas mixtas (ej. carrusel del Home que mezcla
    Consultation + Announcement). Una sola query en vez de unir 4.

    IMPORTANTE: Activity es SOLO-LECTURA. No se instancia directamente.
    Para crear actividades, usar los 4 subtipos concretos.
    """
    objects = ContentManager(content_type=BaseContent.ContentType.ACTIVITY)

    class Meta:
        proxy = True
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "Activity is a read-only umbrella proxy. "
            "To create activities, use Announcement, Consultation, Event or Downloadable."
        )

    @property
    def badge_label(self):
        """Etiqueta de respaldo si no hay subtipo definido."""
        return self.get_subtype_display() or "Actividad"


class Announcement(BaseContent):
    """
    Proxy para Llamados a Concurso / Licitaciones.
    Campos específicos: code, law_reference, contact_email, start_date, end_date, attached_file.
    """
    objects = ActivityManager(subtype=BaseContent.ActivitySubtype.ANNOUNCEMENT)

    class Meta:
        proxy = True
        verbose_name = "Llamado a Concurso"
        verbose_name_plural = "Llamados a Concurso"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.ACTIVITY
        self.subtype = BaseContent.ActivitySubtype.ANNOUNCEMENT
        super().save(*args, **kwargs)

    @property
    def badge_label(self):
        return "Licitación"


class Consultation(BaseContent):
    """
    Proxy para Consultas Públicas.
    Campos específicos: law_reference, contact_email, start_date, end_date, attached_file.
    """
    objects = ActivityManager(subtype=BaseContent.ActivitySubtype.CONSULTATION)

    class Meta:
        proxy = True
        verbose_name = "Consulta Pública"
        verbose_name_plural = "Consultas Públicas"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.ACTIVITY
        self.subtype = BaseContent.ActivitySubtype.CONSULTATION
        super().save(*args, **kwargs)

    @property
    def badge_label(self):
        return "Consulta Pública"

    @property
    def is_open(self):
        """Indica si la consulta está dentro del rango de fechas de vigencia."""
        if not self.start_date or not self.end_date:
            return False
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class Event(BaseContent):
    """
    Proxy para Eventos y Difusión Institucional.
    Campos específicos: image, social_media_url (Instagram, Facebook, etc.).
    """
    objects = ActivityManager(subtype=BaseContent.ActivitySubtype.EVENT)

    class Meta:
        proxy = True
        verbose_name = "Evento / Difusión"
        verbose_name_plural = "Eventos y Difusión"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.ACTIVITY
        self.subtype = BaseContent.ActivitySubtype.EVENT
        super().save(*args, **kwargs)

    @property
    def badge_label(self):
        return "Difusión Institucional"


class Downloadable(BaseContent):
    """
    Proxy para Descargables (PDFs de proyectos, informes, propuestas).

    IMPORTANTE: NO confundir con documents.Document.
    - Downloadable: contenido de difusión del Home (informes, propuestas).
    - Document: documentos oficiales con flujo de aprobación y papelera propia.
    """
    objects = ActivityManager(subtype=BaseContent.ActivitySubtype.DOWNLOADABLE)

    class Meta:
        proxy = True
        verbose_name = "Descargable"
        verbose_name_plural = "Descargables"

    def save(self, *args, **kwargs):
        self.content_type = BaseContent.ContentType.ACTIVITY
        self.subtype = BaseContent.ActivitySubtype.DOWNLOADABLE
        super().save(*args, **kwargs)

    @property
    def badge_label(self):
        return "Descargable"


# ==============================================================================
# 5. MODELOS AUXILIARES
# ==============================================================================

class Category(TimestampedMixin, models.Model):
    """
    Categorías para clasificar noticias y crónicas.
    No es contenido editorial: es una etiqueta reutilizable.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de la Categoría"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name="Slug (URL)"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Commission(TimestampedMixin, models.Model):
    """
    Comisiones permanentes del Concejo (15 en total).

    Cada comisión tiene 3 integrantes fijos: presidente, vicepresidente, vocal.
    Las reglas cross-comisión (un concejal no puede presidir 2 comisiones,
    pero puede ser vocal en varias) se validan en CommissionForm.
    """
    number = models.PositiveIntegerField(unique=True, verbose_name="Número de Comisión")
    name = models.CharField(max_length=250, verbose_name="Nombre de la Comisión")
    description = models.TextField(verbose_name="Área de Trabajo y Funciones")
    image = models.ImageField(
        upload_to='commissions/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Imagen / Foto de la Comisión"
    )

    # 3 FKs fijas → PROTECT: no se puede borrar un concejal con comisiones asignadas.
    president = models.ForeignKey(
        Councilor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'content_type': BaseContent.ContentType.COUNCILOR},
        related_name='commissions_as_president',
        verbose_name="Presidente de la Comisión"
    )
    vice_president = models.ForeignKey(
        Councilor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'content_type': BaseContent.ContentType.COUNCILOR},
        related_name='commissions_as_vicepresident',
        verbose_name="Vicepresidente de la Comisión"
    )
    vocal = models.ForeignKey(
        Councilor,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        limit_choices_to={'content_type': BaseContent.ContentType.COUNCILOR},
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
        """
        Emoji decorativo por número de comisión.

        Cosmético — NO es campo de BD. Si en el futuro se migra a
        FontAwesome, se elimina esta property y se ajusta el template
        commissions.html. Cero migración necesaria.
        """
        emojis = {
            1: '⚖️', 2: '⚽', 3: '🎓', 4: '🏛️', 5: '📐',
            6: '💰', 7: '🔍', 8: '🤝', 9: '📜', 10: '🏗️',
            11: '🚰', 12: '🚌', 13: '🏥', 14: '📡', 15: '🎉',
        }
        return emojis.get(self.number, '📋')


class Legislature(TimestampedMixin, models.Model):
    """
    Períodos legislativos del Concejo.
    Entidad institucional, no contenido editorial → tabla separada.
    """
    roman_id = models.CharField(max_length=10, verbose_name="Número Romano (Ej: VIII)")
    years = models.CharField(max_length=50, verbose_name="Período de Años")
    mayor = models.CharField(max_length=150, verbose_name="Alcalde(sa)")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        verbose_name = "Legislatura"
        verbose_name_plural = "Legislaturas"
        ordering = ['order']

    def __str__(self):
        return f"Legislatura {self.roman_id} ({self.years})"


class Legislator(TimestampedMixin, models.Model):
    """Miembros de una legislatura."""
    legislature = models.ForeignKey(
        Legislature,
        on_delete=models.PROTECT,
        related_name='members',
        verbose_name="Legislatura"
    )
    name = models.CharField(max_length=150, verbose_name="Nombre")
    party = models.CharField(max_length=50, verbose_name="Partido Político")

    class Meta:
        verbose_name = "Legislador"
        verbose_name_plural = "Legisladores"

    def __str__(self):
        return f"{self.name} ({self.party}) - {self.legislature.roman_id}"