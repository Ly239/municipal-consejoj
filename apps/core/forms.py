"""
Copyright [2026] [Proyecto universitario - Concejo Municipal de Junín]

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

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# Modelos locales sincronizados
from .models import (
    BaseContent,
    News,
    Chronicle,
    Category,
    Commission,
    Councilor,
    Legislature,
    AboutUs,
    Activity,
    Announcement,
    Consultation,
    Event,
    Downloadable,
)


# ============================================================
# CLASES BASE DE BOOTSTRAP DINÁMICO
# ============================================================

class BaseBootstrapForm(forms.ModelForm):
    """Clase base para aplicar clases CSS de Bootstrap dinámicamente a los campos."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.BooleanField):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, (forms.DateInput, forms.DateTimeInput)):
                field.widget.attrs.update({'class': 'form-control', 'type': 'date'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class PublicableForm(BaseBootstrapForm):
    """
    Clase base para formularios que usan el sistema automático de publicación.
    Añade un switch de 'Publicar' y maneja is_active y status en el save().
    """
    publicar_ahora = forms.BooleanField(
        required=False, 
        initial=True, 
        label="Publicar inmediatamente",
        help_text="Si se desmarca, se guardará como Borrador (Oculto al público)."
    )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('publicar_ahora'):
            instance.is_active = True
            instance.status = BaseContent.Status.PUBLISHED
        else:
            instance.is_active = False
            instance.status = BaseContent.Status.DRAFT
            
        if commit:
            instance.save()
        return instance


# ============================================================
# 1. NOTICIAS Y CATEGORÍAS
# ============================================================

class NewsForm(PublicableForm):
    """Formulario para la creación y edición de Noticias."""

    class Meta:
        model = News
        fields = [
            'title', 'summary', 'content', 'category', 'image', 
            'attached_file', 'social_media_url'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la noticia'}),
            'summary': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Extracto o resumen breve'}),
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Contenido completo de la publicación'}),
            'image': forms.ClearableFileInput(),
            'attached_file': forms.ClearableFileInput(),
            'social_media_url': forms.URLInput(attrs={'placeholder': 'https://www.instagram.com/p/...'}),
        }


class CategoryForm(BaseBootstrapForm):
    """Formulario para la gestión de Categorías de contenido."""

    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej. Deportes, Economía, Promulgaciones'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance


# ============================================================
# 2. CRÓNICAS Y CONTENIDO INSTITUCIONAL
# ============================================================

class ChronicleForm(PublicableForm):
    """Formulario para la publicación de Crónicas Históricas."""

    class Meta:
        model = Chronicle
        fields = ['title', 'summary', 'content', 'author', 'image', 'attached_file']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la crónica...'}),
            'summary': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Breve introducción o resumen...'}),
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Desarrollo completo de la crónica histórica...'}),
            'author': forms.TextInput(attrs={'placeholder': 'Nombre del cronista o autor'}),
            'image': forms.ClearableFileInput(),
            'attached_file': forms.ClearableFileInput(),
        }


class AboutUsForm(BaseBootstrapForm):
    """Formulario de gestión institucional (Misión, Visión, Quiénes Somos)."""
    class Meta:
        model = AboutUs
        fields = ['title', 'summary', 'content', 'image', 'is_active']


# ============================================================
# 3. COMISIONES, CONCEJALES Y LEGISLATURAS
# ============================================================

class CommissionForm(BaseBootstrapForm):
    """Formulario para la creación y edición de Comisiones Permanentes."""

    class Meta:
        model = Commission
        fields = ['number', 'name', 'description', 'image']
        widgets = {
            'number': forms.NumberInput(attrs={'placeholder': 'Ej. 1'}),
            'name': forms.TextInput(attrs={'placeholder': 'Nombre de la Comisión'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción de la comisión...'}),
            'image': forms.ClearableFileInput(),
        }


class CouncilorForm(PublicableForm):
    """Formulario para la gestión del perfil de Concejales y Directiva."""

    class Meta:
        model = Councilor
        fields = ['title', 'author', 'summary', 'content', 'image', 'social_media_url']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nombre completo del Concejal'}),
            'author': forms.TextInput(attrs={'placeholder': 'Cargo (Ej. Presidente, Concejal Principal)'}),
            'summary': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Resumen biográfico o perfil político'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Trayectoria, comisiones que integra y logros'}),
            'image': forms.ClearableFileInput(),
            'social_media_url': forms.URLInput(attrs={'placeholder': 'Enlace a perfil institucional'}),
        }


class LegislatureForm(BaseBootstrapForm):
    """Formulario para el registro de Períodos Legislativos e Históricos."""

    class Meta:
        model = Legislature
        fields = ['roman_id', 'years', 'mayor', 'order']
        widgets = {
            'roman_id': forms.TextInput(attrs={'placeholder': 'Ej. I, II, III'}),
            'years': forms.TextInput(attrs={'placeholder': 'Ej. 2021 - 2025'}),
            'mayor': forms.TextInput(attrs={'placeholder': 'Nombre del Alcalde del período'}),
            'order': forms.NumberInput(attrs={'placeholder': 'Ej. 1'}),
        }


# ============================================================
# 4. ACTIVIDADES, EVENTOS Y PARTICIPACIÓN
# ============================================================

class ActivityForm(BaseBootstrapForm):
    class Meta:
        model = Activity
        fields = '__all__'


class EventForm(PublicableForm):
    """Formulario para la programación de Eventos Públicos."""

    class Meta:
        model = Event
        fields = ['title', 'summary', 'content', 'start_date', 'end_date', 'image', 'attached_file']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nombre del evento'}),
            'summary': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Descripción breve'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Agenda o itinerario detallado'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}), # Corregido a type='date'
            'end_date': forms.DateInput(attrs={'type': 'date'}),   # Corregido a type='date'
            'image': forms.ClearableFileInput(),
            'attached_file': forms.ClearableFileInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise ValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio.")
        return cleaned_data


class AnnouncementForm(PublicableForm):
    """Formulario para Licitaciones y Convocatorias Oficiales."""

    class Meta:
        model = Announcement
        fields = ['title', 'summary', 'content', 'attached_file', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la licitación o convocatoria'}),
            'summary': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Objeto del proceso'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Bases y condiciones generales'}),
            'attached_file': forms.ClearableFileInput(),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise ValidationError("La fecha de recepción/cierre debe ser posterior al inicio.")
        return cleaned_data


class ConsultationForm(PublicableForm):
    """Formulario para Consultas Públicas Abiertas a la Comunidad."""

    class Meta:
        model = Consultation
        fields = ['title', 'summary', 'content', 'attached_file', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la consulta ciudadana'}),
            'summary': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Propósito de la consulta'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Texto del anteproyecto u ordenanza'}),
            'attached_file': forms.ClearableFileInput(),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end < start:
            raise ValidationError("La fecha de cierre de la consulta debe ser posterior a la fecha de apertura.")
        return cleaned_data


# ============================================================
# 5. DOCUMENTOS DESCARGABLES
# ============================================================

class DownloadableForm(PublicableForm):
    """Formulario para la carga de Documentos y Formatos Descargables."""

    class Meta:
        model = Downloadable
        fields = ['title', 'summary', 'category', 'attached_file', 'year']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nombre del documento o formato'}),
            'summary': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Instrucciones o descripción del archivo'}),
            'attached_file': forms.ClearableFileInput(),
            'year': forms.TextInput(attrs={'placeholder': 'Ej. 2026'}),
        }