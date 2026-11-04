from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import (
    BaseContent, News, Chronicle, Category, Commission, Councilor,
    Legislature, AboutUs, Activity, Announcement, Consultation, Event, Downloadable,
)

class BaseBootstrapForm(forms.ModelForm):
    """Clase base para aplicar clases CSS de Bootstrap y type='date' dinámicamente."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, (forms.DateInput, forms.DateTimeInput)):
                field.widget.attrs.update({'class': 'form-control', 'type': 'date'}) # CALENDARIO
                field.input_formats = ['%Y-%m-%d']
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

class PublicableForm(BaseBootstrapForm):
    """Añade el switch de 'Publicar' y maneja is_active/status en el save()."""
    publicar_ahora = forms.BooleanField(
        required=False, initial=True, label="Publicar inmediatamente",
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

# --- FORMULARIOS ---

class NewsForm(PublicableForm):
    class Meta:
        model = News
        fields = ['title', 'summary', 'content', 'category', 'image', 'attached_file', 'social_media_url']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la noticia'}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 6}),
            'social_media_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

class ChronicleForm(PublicableForm):
    class Meta:
        model = Chronicle
        fields = ['title', 'summary', 'content', 'author', 'image', 'attached_file', 'social_media_url'] # 🆕 URL agregada
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la crónica...'}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 6}),
            'social_media_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

class EventForm(PublicableForm):
    class Meta:
        model = Event
        fields = ['title', 'summary', 'content', 'start_date', 'end_date', 'image', 'attached_file']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nombre del evento'}),
            'summary': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 5}),
        }
    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get('start_date'), cleaned_data.get('end_date')
        if start and end and end < start:
            raise ValidationError("La fecha de finalización no puede ser anterior a la de inicio.")
        return cleaned_data

class AnnouncementForm(PublicableForm):
    class Meta:
        model = Announcement
        fields = ['title', 'summary', 'content', 'attached_file', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la licitación'}),
            'summary': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 5}),
        }
    def clean(self):
        cleaned_data = super().clean()
        start, end = cleaned_data.get('start_date'), cleaned_data.get('end_date')
        if start and end and end < start:
            raise ValidationError("La fecha de cierre debe ser posterior al inicio.")
        return cleaned_data

class ConsultationForm(PublicableForm):
    class Meta:
        model = Consultation
        fields = ['title', 'summary', 'content', 'attached_file', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la consulta'}),
            'summary': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class DownloadableForm(PublicableForm):
    class Meta:
        model = Downloadable
        fields = ['title', 'summary', 'category', 'attached_file', 'year']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nombre del documento'}),
            'summary': forms.Textarea(attrs={'rows': 2}),
            'year': forms.TextInput(attrs={'placeholder': 'Ej. 2026'}),
        }

class CouncilorForm(PublicableForm):
    class Meta:
        model = Councilor
        fields = ['title', 'author', 'summary', 'content', 'image', 'social_media_url']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'author': forms.TextInput(attrs={'placeholder': 'Cargo (Ej. Presidente)'}),
            'summary': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 5}),
            'social_media_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

class CategoryForm(BaseBootstrapForm):
    class Meta:
        model = Category
        fields = ['name']
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = slugify(instance.name)
        if commit: instance.save()
        return instance

class CommissionForm(BaseBootstrapForm):
    class Meta:
        model = Commission
        fields = ['number', 'name', 'description', 'image']

class LegislatureForm(BaseBootstrapForm):
    class Meta:
        model = Legislature
        fields = ['roman_id', 'years', 'mayor', 'order']

class AboutUsForm(BaseBootstrapForm):
    class Meta:
        model = AboutUs
        fields = ['title', 'summary', 'content', 'image', 'is_active']

class ActivityForm(BaseBootstrapForm):
    class Meta:
        model = Activity
        fields = '__all__'