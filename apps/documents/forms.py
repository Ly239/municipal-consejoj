import os
import re
import logging
from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date
from .models import Gazette, Document, DocumentType, IssuingEntity
from common.validators import validate_unique_with_trash

logger = logging.getLogger(__name__)


# ==================================================
# 1. MIXIN PARA CAMPOS DE FECHA
# ==================================================
class DateFieldMixin:
    """
    Mixin que configura los campos DateField para usar input type='date'
    y formato 'YYYY-MM-DD'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.DateField):
                field.input_formats = ['%Y-%m-%d']
                if isinstance(field.widget, forms.DateInput):
                    field.widget.attrs.update({'type': 'date', 'class': 'form-control'})
                    field.widget.input_type = 'date'
                    field.widget.format = '%Y-%m-%d'


# ==================================================
# 2. FUNCIONES DE VALIDACIÓN REUTILIZABLES
# ==================================================

def validate_positive_number(value, field_name="Número"):
    """Valida que el valor sea un número entero positivo."""
    try:
        if value is not None and value <= 0:
            raise ValidationError(f"{field_name} debe ser un número positivo.")
        return value
    except Exception as e:
        logger.error(f"Error en validate_positive_number: {e}")
        raise

#ESTA FUNCIÓN SE PUEDE OPTIMIZAR
def validate_max_number(value, max_value, field_name="Número"):
    """
    Valida que el número esté dentro del rango permitido.
    Rechaza números gigantes antes de que lleguen a la BD.
    """
    if value is None:
        return value
    if value <= 0:
        raise ValidationError(f"{field_name} debe ser un número positivo.")
    if value > max_value:
        raise ValidationError(
            f"{field_name} no puede superar {max_value}. "
            f"El máximo permitido es {max_value}."
        )
    return value


def validate_future_date(value, field_name="Fecha"):
    """Valida que la fecha no sea futura."""
    try:
        if value and value > date.today():
            raise ValidationError(f"{field_name} no puede ser una fecha futura.")
        return value
    except Exception as e:
        logger.error(f"Error en validate_future_date: {e}")
        raise


def validate_year(value, field_name="Año"):
    """Valida que el año sea válido (entre 1900 y el año actual + 1)."""
    try:
        current_year = date.today().year
        if value and (value < 1900 or value > current_year + 1):
            raise ValidationError(
                f"{field_name} debe estar entre 1900 y {current_year + 1}."
            )
        return value
    except Exception as e:
        logger.error(f"Error en validate_year: {e}")
        raise


# Extensiones permitidas para cada campo
ALLOWED_PDF_EXTENSIONS = ['.pdf']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
MAX_PDF_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_pdf_file(value):
    """Valida que el archivo sea un PDF y no exceda el tamaño máximo."""
    try:
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_PDF_EXTENSIONS:
            raise ValidationError('Solo se permiten archivos PDF en este campo.')

        if value.size > MAX_PDF_SIZE:
            raise ValidationError(f'El archivo no puede exceder los {MAX_PDF_SIZE // (1024*1024)} MB.')
    except Exception as e:
        logger.error(f"Error en validate_pdf_file: {e}")
        raise ValidationError("Error al validar el archivo PDF.")


def validate_image_file(value):
    """Valida que el archivo sea una imagen."""
    try:
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError('Solo se permiten archivos de imagen (JPG, PNG, GIF, BMP, WEBP) en este campo.')
    except Exception as e:
        logger.error(f"Error en validate_image_file: {e}")
        raise ValidationError("Error al validar el archivo de imagen.")


# ==================================================
# 3. FORMULARIO PARA GACETA
# ==================================================
class GazetteForm(DateFieldMixin, forms.ModelForm):
    """Formulario para crear y editar Gacetas."""

    class Meta:
        model = Gazette
        fields = ['number', 'year', 'is_extraordinary', 'emission_date', 'description']
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 248'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2026'
            }),
            'is_extraordinary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'emission_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Breve descripción del contenido de la gaceta (opcional)'
            }),
        }
        labels = {
            'number': 'Número de Gaceta',
            'year': 'Año',
            'is_extraordinary': '¿Extraordinaria?',
            'emission_date': 'Fecha de Emisión',
            'description': 'Descripción',
        }
        help_texts = {
            'number': 'Número consecutivo de la gaceta en el año. Máximo 500.',
            'year': 'Año de publicación.',
            'is_extraordinary': 'Marque si la gaceta es extraordinaria (fuera de la periodicidad regular).',
            'emission_date': 'Fecha oficial de emisión de la gaceta.',
            'description': 'Resumen opcional del contenido de la gaceta.',
        }

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
            # Pre-cargar año actual si no existe
            if not self.instance.pk and not self.initial.get('year'):
                self.initial['year'] = date.today().year
        except Exception as e:
            logger.error(f"Error en __init__ de GazetteForm: {e}")
            raise

    def validate_unique(self):
        """
        Deshabilitar validación automática de unique_together.

        Motivo: la unicidad de (number, year, is_extraordinary) se valida
        manualmente en clean() para considerar registros en la papelera (soft delete).
        Django, por defecto, NO considera la papelera → genera mensaje duplicado.

        ⚠️ Si en el futuro se agrega un campo con unique=True individual,
        habrá que validarlo manualmente en clean_<campo>().
        """
        pass


    def clean_number(self):
        """Valida que el número sea positivo y no supere el máximo."""
        try:
            return validate_max_number(
                self.cleaned_data.get('number'),
                max_value=500,
                field_name="El número de gaceta"
            )
        except Exception as e:
            logger.error(f"Error en clean_number de GazetteForm: {e}")
            raise

    def clean_year(self):
        """Valida que el año sea válido y no futuro."""
        try:
            year = self.cleaned_data.get('year')
            return validate_year(year, "El año")
        except Exception as e:
            logger.error(f"Error en clean_year de GazetteForm: {e}")
            raise

    def clean_emission_date(self):
        """Valida que la fecha de emisión no sea futura."""
        try:
            emission_date = self.cleaned_data.get('emission_date')
            if emission_date:
                return validate_future_date(emission_date, "La fecha de emisión")
            return emission_date
        except Exception as e:
            logger.error(f"Error en clean_emission_date de GazetteForm: {e}")
            raise

    def clean(self):
        """
        Validaciones cruzadas:
        - Unicidad de (number, year, is_extraordinary) considerando papelera.
        """
        try:
            cleaned_data = super().clean()
            number = cleaned_data.get('number')
            year = cleaned_data.get('year')
            is_extraordinary = cleaned_data.get('is_extraordinary')

            if number and year:
                # Validar unicidad considerando papelera
                existing = Gazette.all_objects.filter(
                    number=number,
                    year=year,
                    is_extraordinary=is_extraordinary
                ).first()

                if self.instance.pk:
                    existing = Gazette.all_objects.filter(
                        number=number,
                        year=year,
                        is_extraordinary=is_extraordinary
                    ).exclude(pk=self.instance.pk).first()

                if existing:
                    if existing.is_deleted:
                        raise ValidationError(
                            f"Ya existe una gaceta con el número {number}, año {year} y tipo {'Extraordinaria' if is_extraordinary else 'Ordinaria'} en la papelera. "
                            "Restáurala o elimínala definitivamente."
                        )
                    else:
                        raise ValidationError(
                            f"Ya existe una gaceta con el número {number}, año {year} y tipo {'Extraordinaria' if is_extraordinary else 'Ordinaria'}."
                        )
            return cleaned_data
        except Exception as e:
            logger.error(f"Error en clean de GazetteForm: {e}")
            raise


# ==================================================
# 4. FORMULARIO PARA DOCUMENTO
# ==================================================
class DocumentForm(DateFieldMixin, forms.ModelForm):
    """Formulario para crear y editar Documentos."""

    class Meta:
        model = Document
        fields = [
            'gazette', 'document_type', 'issuing_entity',
            'number', 'title', 'description',
            'emission_date', 'is_approved', 'is_annulled',
            'pdf_file', 'image', 'other_entity_description'
        ]
        widgets = {
            'gazette': forms.Select(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'issuing_entity': forms.Select(attrs={'class': 'form-control'}),
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 102'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del documento'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Reseña detallada del documento'
            }),
            'emission_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'is_approved': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_annulled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'other_entity_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Especificar si el ente emisor es "Otros"'
            }),
        }
        labels = {
            'gazette': 'Gaceta',
            'document_type': 'Tipo de Documento',
            'issuing_entity': 'Ente Emisor',
            'number': 'Número de Documento',
            'title': 'Título',
            'description': 'Descripción / Reseña',
            'emission_date': 'Fecha de Emisión',
            'is_approved': '¿Aprobado?',
            'is_annulled': '¿Anulado?',
            'pdf_file': 'Archivo PDF',
            'image': 'Imagen (opcional)',
            'other_entity_description': 'Otro Ente (especificar)',
        }
        help_texts = {
            'number': 'Número consecutivo del documento en el año. Máximo 1000.',
            'emission_date': 'Fecha en que se emitió el documento en físico.',
            'is_approved': 'Marcar si el documento ya está aprobado.',
            'is_annulled': 'Marcar si el documento ha sido anulado.',
            'pdf_file': 'Subir el documento en formato PDF (opcional). Máximo 10 MB.',
            'image': 'Subir una foto del documento físico (opcional).',
            'other_entity_description': 'Requerido si selecciona "Otros" como ente emisor.',
        }

    def __init__(self, *args, **kwargs):
        try:
            super().__init__(*args, **kwargs)
            # Hacer que el campo 'other_entity_description' no sea obligatorio inicialmente
            # La validación condicional se hará en clean()
            self.fields['other_entity_description'].required = False
        except Exception as e:
            logger.error(f"Error en __init__ de DocumentForm: {e}")
            raise

    def validate_unique(self):
        """
        Deshabilitar validación automática de unique_together.

        Motivo: la unicidad de (number, gazette) se valida manualmente en clean()
        para considerar registros en la papelera (soft delete). Django, por
        defecto, NO considera la papelera → genera mensaje duplicado.

        ⚠️ Si en el futuro se agrega un campo con unique=True individual,
        habrá que validarlo manualmente en clean_<campo>().
        """
        pass


    def clean_number(self):
        """Valida que el número sea positivo y no supere el máximo."""
        try:
            return validate_max_number(
                self.cleaned_data.get('number'),
                max_value=1000,
                field_name="El número de documento"
            )
        except Exception as e:
            logger.error(f"Error en clean_number de DocumentForm: {e}")
            raise

    def clean_emission_date(self):
        """Valida que la fecha de emisión no sea futura."""
        try:
            emission_date = self.cleaned_data.get('emission_date')
            if emission_date:
                return validate_future_date(emission_date, "La fecha de emisión")
            return emission_date
        except Exception as e:
            logger.error(f"Error en clean_emission_date de DocumentForm: {e}")
            raise

    def clean_pdf_file(self):
        """Valida que el archivo sea un PDF y no exceda el tamaño máximo."""
        try:
            file = self.cleaned_data.get('pdf_file')
            if file:
                validate_pdf_file(file)
            return file
        except Exception as e:
            logger.error(f"Error en clean_pdf_file de DocumentForm: {e}")
            raise

    def clean_image(self):
        """Valida que el archivo sea una imagen."""
        try:
            file = self.cleaned_data.get('image')
            if file:
                validate_image_file(file)
            return file
        except Exception as e:
            logger.error(f"Error en clean_image de DocumentForm: {e}")
            raise

    def clean(self):
        """
        Validaciones cruzadas:
        1. Si 'issuing_entity' es "Otros", 'other_entity_description' es obligatorio.
        2. Unicidad de número de documento dentro de la gaceta (considerando papelera).
        3. El año del documento debe coincidir con el año de la gaceta.
        4. Un documento no puede estar aprobado y anulado al mismo tiempo.
        """
        try:
            cleaned_data = super().clean()
            gazette = cleaned_data.get('gazette')
            number = cleaned_data.get('number')
            issuing_entity = cleaned_data.get('issuing_entity')
            other_desc = cleaned_data.get('other_entity_description')
            emission_date = cleaned_data.get('emission_date')
            is_approved = cleaned_data.get('is_approved')
            is_annulled = cleaned_data.get('is_annulled')

            # 1. Validación de "Otros" ente emisor
            if issuing_entity and issuing_entity.name == "Otros":
                if not other_desc or other_desc.strip() == '':
                    self.add_error(
                        'other_entity_description',
                        'Debe especificar el nombre del ente emisor cuando selecciona "Otros".'
                    )

            # 2. Unicidad de número dentro de la gaceta (considerando papelera)
            if gazette and number:
                existing = Document.all_objects.filter(number=number, gazette=gazette).first()
                if self.instance.pk:
                    existing = Document.all_objects.filter(
                        number=number,
                        gazette=gazette
                    ).exclude(pk=self.instance.pk).first()

                if existing:
                    if existing.is_deleted:
                        raise ValidationError(
                            f"Ya existe un documento con el número {number} en la gaceta {gazette} en la papelera. "
                            "Restáuralo o elimínalo definitivamente."
                        )
                    else:
                        raise ValidationError(
                            f"Ya existe un documento con el número {number} en la gaceta {gazette}."
                        )

            # 3. El año del documento debe coincidir con el año de la gaceta
            if gazette and emission_date:
                if emission_date.year != gazette.year:
                    self.add_error(
                        'emission_date',
                        f"El año de emisión ({emission_date.year}) no coincide con el año de la gaceta ({gazette.year})."
                    )

            # 4. Un documento no puede estar aprobado y anulado al mismo tiempo
            if is_approved and is_annulled:
                self.add_error(
                    'is_approved',
                    "Un documento no puede estar aprobado y anulado al mismo tiempo."
                )

            return cleaned_data
        except Exception as e:
            logger.error(f"Error en clean de DocumentForm: {e}")
            raise