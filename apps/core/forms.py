from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import (
    BaseContent, News, Chronicle, Category, Commission, Councilor,
    Legislature, AboutUs, Activity, Announcement, Consultation, Event, Downloadable, Legislator, 
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
        fields = ['title', 'summary', 'content', 'author', 'image', 'attached_file', 'social_media_url'] #  URL agregada
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
        # Agregamos code y law_reference
        fields = ['title', 'summary', 'content', 'code', 'law_reference', 'attached_file', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Título de la licitación'}),
            'summary': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 5}),
            'code': forms.TextInput(attrs={'placeholder': 'Ej. CMEH/CCP/CA/2026/008'}),
            'law_reference': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej. Artículos 78, 79 y 80...'}),
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
    CARGOS = [
        ('Presidente', 'Presidente'),
        ('Vicepresidente', 'Vicepresidente'),
        ('Concejal', 'Concejal'),
        ('Síndico Procurador', 'Síndico Procurador'),
        ('Secretario(a)', 'Secretario(a)'),
    ]
    
    author = forms.ChoiceField(choices=CARGOS, label="Cargo", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Councilor
        fields = ['title', 'author', 'summary', 'content', 'image', 'social_media_url']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'summary': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Resumen para la tarjeta pública'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Trayectoria o perfil completo'}),
            'image': forms.ClearableFileInput(),
            'social_media_url': forms.URLInput(attrs={'placeholder': 'https://instagram.com/...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # SALVAVIDAS: Si el dato viejo no está en la lista, lo inyectamos temporalmente
        if self.instance and self.instance.pk and self.instance.author:
            current_author = self.instance.author
            choices = list(self.fields['author'].choices)
            if current_author not in [c[0] for c in choices]:
                choices.append((current_author, current_author))
                self.fields['author'].choices = choices
    
    def clean_author(self):
        """Valida que no existan cargos únicos duplicados."""
        author = self.cleaned_data.get('author')
        
        # Validamos que solo haya un Presidente, un Vice y un Secretario(a)
        if author in ['Presidente', 'Vicepresidente', 'Secretario(a)']:
            # Buscamos si ya existe alguien con ese cargo (excluyendo el actual si estamos editando)
            exists = Councilor.objects.filter(author=author, is_active=True).exclude(pk=self.instance.pk).exists()
            if exists:
                raise forms.ValidationError(f"Ya existe un {author} registrado. Si deseas cambiarlo, edita el registro anterior.")
        
        return author
        

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
        # Agregamos las 3 FKs para que salgan en el desplegable
        fields = ['number', 'name', 'description', 'image', 'president', 'vice_president', 'vocal'] 

    def clean(self):
        """Valida que un mismo concejal no ocupe más de un cargo en la misma comisión."""
        cleaned_data = super().clean()
        president = cleaned_data.get('president')
        vice_president = cleaned_data.get('vice_president')
        vocal = cleaned_data.get('vocal')

        # Validaciones cruzadas
        if president and vice_president and president == vice_president:
            self.add_error('vice_president', "El vicepresidente no puede ser la misma persona que el presidente.")
        
        if president and vocal and president == vocal:
            self.add_error('vocal', "El vocal no puede ser la misma persona que el presidente.")
        
        if vice_president and vocal and vice_president == vocal:
            self.add_error('vocal', "El vocal no puede ser la misma persona que el vicepresidente.")

        return cleaned_data



class LegislatureForm(BaseBootstrapForm):
    """Formulario para Legislaturas con creación KISS de legisladores."""
    
    lista_legisladores = forms.CharField(
        required=False,
        label="Lista de Legisladores",
        help_text="Separa los nombres por comas. Ejemplo: Juan Pérez (Partido A), María Gómez (Partido B). Si no pones el partido entre paréntesis, se guardará como 'Independiente'.",
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Juan Pérez (AD), María Gómez (PSUV)...'})
    )

    class Meta:
        model = Legislature
        fields = ['roman_id', 'years', 'mayor']
        widgets = {
            'roman_id': forms.TextInput(attrs={'placeholder': 'Ej. I, II, III'}),
            'years': forms.TextInput(attrs={'placeholder': 'Ej. 2021 - 2025'}),
            'mayor': forms.TextInput(attrs={'placeholder': 'Nombre del Alcalde del período'}),
            'order': forms.NumberInput(attrs={'placeholder': 'Ej. 1'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando, precargamos los legisladores existentes en el textarea
        if self.instance and self.instance.pk:
            miembros = self.instance.members.all()
            if miembros.exists():
                nombres = [f"{m.name} ({m.party})" for m in miembros]
                self.initial['lista_legisladores'] = ", ".join(nombres)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Lógica para procesar el texto y crear los legisladores
            texto = self.cleaned_data.get('lista_legisladores')
            if texto is not None:
                # Borramos los anteriores para que no se dupliquen al editar
                instance.members.all().delete()
                
                # Separamos por comas y creamos los nuevos
                items = texto.split(',')
                for item in items:
                    item = item.strip()
                    if item:
                        # Intentamos extraer el partido entre paréntesis
                        if '(' in item and item.endswith(')'):
                            nombre, partido = item.split('(', 1)
                            partido = partido.rstrip(')').strip()
                        else:
                            nombre = item
                            partido = "Independiente"
                        
                        Legislator.objects.create(
                            legislature=instance,
                            name=nombre.strip(),
                            party=partido
                        )
        return instance



class AboutUsForm(BaseBootstrapForm):
    class Meta:
        model = AboutUs
        fields = ['title', 'summary', 'content', 'image', 'is_active']

class ActivityForm(BaseBootstrapForm):
    class Meta:
        model = Activity
        fields = '__all__'