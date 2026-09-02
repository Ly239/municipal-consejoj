"""
Modelos para la gestión de documentos
Incluye: Gaceta, Documento, Tipos de Documento y Entes Emisores.
"""
from django.db import models
from common.models import BaseModel
from django.contrib.auth import get_user_model

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
    number = models.PositiveIntegerField(verbose_name="Número")
    year = models.PositiveIntegerField(verbose_name="Año")
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        unique_together = ['number', 'year']
        verbose_name = "Gaceta"
        verbose_name_plural = "Gacetas"
        ordering = ['-year', '-number']

    def __str__(self):
        return f"Gaceta N° {self.number} - {self.year}"

    @property
    def has_documents(self):
        """Indica si la gaceta tiene al menos un documento asociado."""
        return self.documents.exists()


# ------------------------------------------------------------------------
# 3. TABLA PRINCIPAL: DOCUMENTO
# ------------------------------------------------------------------------
class Document(BaseModel):
    
    # Relaciones (TODAS CON PROTECT)
    gazette = models.ForeignKey(
        Gazette,
        on_delete=models.PROTECT,  # 🛡️ No permite borrar si hay documentos
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
    number = models.PositiveIntegerField(verbose_name="Número de Documento")
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción / Reseña")
    emission_date = models.DateField(verbose_name="Fecha de Emisión")
    publication_date = models.DateField(auto_now_add=True, verbose_name="Fecha de Publicación")
    is_approved = models.BooleanField(default=False, verbose_name="¿Aprobado?")

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

    def __str__(self):
        return f"{self.document_type.name} N° {self.number:04d}-{self.gazette.year}"

    @property
    def year(self):
        """Año del documento (obtenido desde la gaceta)."""
        return self.gazette.year