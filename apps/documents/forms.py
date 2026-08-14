import re
from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date
from .models import Gazette, Document, DocumentType, IssuingEntity


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
    if value is not None and value <= 0:
        raise ValidationError(f"{field_name} debe ser un número positivo.")
    return value


def validate_future_date(value, field_name="Fecha"):
    """Valida que la fecha no sea futura."""
    if value and value > date.today():
        raise ValidationError(f"{field_name} no puede ser una fecha futura.")
    return value


def validate_year(value, field_name="Año"):
    """Valida que el año sea válido (entre 1900 y el año actual + 1)."""
    current_year = date.today().year
    if value and (value < 1900 or value > current_year + 1):
        raise ValidationError(
            f"{field_name} debe estar entre 1900 y {current_year + 1}."
        )
    return value


# ==================================================
# 3. FORMULARIO PARA GACETA
# ==================================================
class GazetteForm(DateFieldMixin, forms.ModelForm):
    """Formulario para crear y editar Gacetas."""
    
    class Meta:
        model = Gazette
        fields = ['number', 'year', 'description']
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 248'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2026'
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
            'description': 'Descripción',
        }
        help_texts = {
            'number': 'Número consecutivo de la gaceta en el año.',
            'year': 'Año de publicación.',
            'description': 'Resumen opcional del contenido de la gaceta.',
        }

    def clean_number(self):
        """Valida que el número sea positivo."""
        return validate_positive_number(
            self.cleaned_data.get('number'),
            "El número de gaceta"
        )

    def clean_year(self):
        """Valida que el año sea válido y no futuro."""
        year = self.cleaned_data.get('year')
        year = validate_year(year, "El año")
        return year

    def clean(self):
        """
        Valida que no exista otra gaceta con el mismo número y año.
        """
        cleaned_data = super().clean()
        number = cleaned_data.get('number')
        year = cleaned_data.get('year')

        if number and year:
            # Verificar unicidad (excluyendo el propio objeto si es edición)
            qs = Gazette.objects.filter(number=number, year=year)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f"Ya existe una gaceta con el número {number} y año {year}."
                )

        return cleaned_data


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
            'emission_date', 'is_approved',
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
            'pdf_file': 'Archivo PDF',
            'image': 'Imagen (opcional)',
            'other_entity_description': 'Otro Ente (especificar)',
        }
        help_texts = {
            'number': 'Número consecutivo del documento en el año.',
            'emission_date': 'Fecha en que se emitió el documento en físico.',
            'is_approved': 'Marcar si el documento ya está aprobado.',
            'pdf_file': 'Subir el documento en formato PDF (opcional).',
            'image': 'Subir una foto del documento físico (opcional).',
            'other_entity_description': 'Requerido si selecciona "Otros" como ente emisor.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que el campo 'other_entity_description' no sea obligatorio inicialmente
        # La validación condicional se hará en clean()
        self.fields['other_entity_description'].required = False

    def clean_number(self):
        """Valida que el número sea positivo."""
        return validate_positive_number(
            self.cleaned_data.get('number'),
            "El número de documento"
        )

    def clean_emission_date(self):
        """
        Valida que la fecha de emisión no sea futura.
        """
        emission_date = self.cleaned_data.get('emission_date')
        if emission_date:
            # Validar que no sea futura
            if emission_date > date.today():
                raise ValidationError("La fecha de emisión no puede ser una fecha futura.")
        return emission_date

    def clean(self):
        """
        Validaciones cruzadas:
        1. Si 'issuing_entity' es "Otros", 'other_entity_description' es obligatorio.
        2. Unicidad de número de documento dentro de la gaceta.
        3. La fecha de emisión debe ser anterior a la fecha de publicación (si existe).
        4. El año del documento debe coincidir con el año de la gaceta.
        """
        cleaned_data = super().clean()
        gazette = cleaned_data.get('gazette')
        number = cleaned_data.get('number')
        issuing_entity = cleaned_data.get('issuing_entity')
        other_desc = cleaned_data.get('other_entity_description')
        emission_date = cleaned_data.get('emission_date')
        publication_date = cleaned_data.get('publication_date')  # No está en el form, se asigna automáticamente

        # 1. Validación de "Otros" ente emisor
        if issuing_entity and issuing_entity.name == "Otros":
            if not other_desc or other_desc.strip() == '':
                self.add_error(
                    'other_entity_description',
                    'Debe especificar el nombre del ente emisor cuando selecciona "Otros".'
                )

        # 2. Unicidad de número dentro de la gaceta
        if gazette and number:
            qs = Document.objects.filter(gazette=gazette, number=number)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    'number',
                    f"Ya existe un documento con el número {number} en la gaceta {gazette}."
                )

        # 3. El año del documento debe coincidir con el año de la gaceta
        if gazette and emission_date:
            if emission_date.year != gazette.year:
                self.add_error(
                    'emission_date',
                    f"El año de emisión ({emission_date.year}) no coincide con el año de la gaceta ({gazette.year})."
                )

        return cleaned_data

