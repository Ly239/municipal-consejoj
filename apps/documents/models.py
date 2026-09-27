"""
Modelos para la gestión de documentos
Incluye: Gaceta, Documento, Tipos de Documento y Entes Emisores.
"""
import logging
from django.db import models
from common.models import BaseModel
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator

#Para capturar errores
logger = logging.getLogger(__name__)

#usuario filtrar
User = get_user_model()


# ------------------------------------------------------------------------
# 1. TABLAS SEEDER (sin dependencias externas)
# ------------------------------------------------------------------------
class DocumentType(BaseModel):
    """Catálogo de tipos de documentos legales (Acuerdo, Ordenanza, etc.)."""
    include_in_trash = False  # no aparece en la papelera universal

    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Tipo de Documento"
        verbose_name_plural = "Tipos de Documentos"
        ordering = ['name']

    def __str__(self):
        return self.name


class IssuingEntity(BaseModel):
    """Catálogo de entes emisores de documentos."""

    include_in_trash = False

    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Ente Emisor"
        verbose_name_plural = "Entes Emisores"
        ordering = ['name']

    def __str__(self):
        return self.name




# ------------------------------------------------------------------------
# 2. TABLA PRINCIPAL: GACETA
# ------------------------------------------------------------------------
class Gazette(BaseModel):
    """
    Gaceta Municipal: agrupa documentos por número y año.
    Puede existir sin documentos asociados.
    """
    # Límite máximo de 500 gacetas por año
    number = models.PositiveIntegerField(
        validators=[MaxValueValidator(500)],
        verbose_name="Número"
    )
    year = models.PositiveIntegerField(verbose_name="Año")
    is_extraordinary = models.BooleanField(
        default=False,
        verbose_name="¿Extraordinaria?"
    )
    emission_date = models.DateField(
        verbose_name="Fecha de Emisión"
    )
    
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        unique_together = ['number', 'year', 'is_extraordinary']
        verbose_name = "Gaceta"
        verbose_name_plural = "Gacetas"
        ordering = ['year', 'number']

    def __str__(self):
        tipo = "Extraordinaria" if self.is_extraordinary else "Ordinaria"
        return f"Gaceta {tipo} N° {self.number:03d}-{self.year}"

    @property
    def publication_date(self):
        """
        Alias semántico de created_at.
        Mantiene compatibilidad con templates y admin que usan
        'publication_date' para referirse a la fecha de publicación en el sistema.
        El dato real vive en created_at (heredado de BaseModel, DateTimeField).
        """
        return self.created_at

    @property
    def formatted_number(self):
        """Devuelve el número con ceros a la izquierda (001, 002, ..., 500)."""
        return f"{self.number:03d}"

    @property
    def has_documents(self):
        """Indica si la gaceta tiene al menos un documento asociado."""
        return self.documents.exists()

    def save(self, *args, **kwargs):
        """Sobrescritura con try-except para manejar errores de integridad."""
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error al guardar Gaceta: {e}")
            raise


# ------------------------------------------------------------------------
# 3. TABLA PRINCIPAL: DOCUMENTO
# ------------------------------------------------------------------------
class Document(BaseModel):

    # Relaciones (TODAS CON PROTECT)
    gazette = models.ForeignKey(
        Gazette,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name="Gaceta"
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name="Tipo de Documento"
    )
    issuing_entity = models.ForeignKey(
        IssuingEntity,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name="Ente Emisor"
    )
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='submitted_documents',
        verbose_name="Subido por"
    )

    # Campos principales
    # Límite máximo de 1000 documentos por gaceta
    number = models.PositiveIntegerField(
        validators=[MaxValueValidator(1000)],
        verbose_name="Número de Documento"
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción / Reseña")
    emission_date = models.DateField(verbose_name="Fecha de Emisión")
    

    # Estado: booleano (más fácil de filtrar)
    is_approved = models.BooleanField(default=False, verbose_name="¿Aprobado?")
    is_annulled = models.BooleanField(default=False, verbose_name="¿Anulado?")

    # Archivos adjuntos
    pdf_file = models.FileField(
        upload_to='documents/pdfs/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Archivo PDF"
    )
    image = models.ImageField(
        upload_to='documents/images/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Imagen"
    )

    # Campo opcional para "Otros" entes emisores
    other_entity_description = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Otro Ente (especificar)"
    )

    class Meta:
        unique_together = ['number', 'gazette']
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-emission_date']

        # Restricción de integridad a nivel de BD
        constraints = [
            models.CheckConstraint(
                check=~models.Q(is_approved=True, is_annulled=True),
                name="document_no_approved_and_annulled"
            )
        ]

    def __str__(self):
        estado = "✓" if self.is_approved else ("✗" if self.is_annulled else "⏳")
        return f"{self.document_type.name} N° {self.number:03d}-{self.gazette.year} [{estado}]"

    @property
    def publication_date(self):
        """Alias semántico de created_at (fecha de publicación en el sistema)."""
        return self.created_at

    @property
    def year(self):
        """Año del documento (obtenido desde la gaceta)."""
        return self.gazette.year

    @property
    def formatted_number(self):
        """Devuelve el número con ceros a la izquierda (001, 002, ..., 1000)."""
        return f"{self.number:03d}"

    def save(self, *args, **kwargs):
        """Sobrescritura con try-except para manejar errores de integridad."""
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error al guardar Documento: {e}")
            raise