from django import forms
from django.utils.text import slugify
from .models import HomeCarouselNews, MunicipalChronicle, Category



class HomeCarouselNewsForm(forms.ModelForm):
    class Meta:
        model = HomeCarouselNews
        fields = ['title', 'summary', 'content', 'category', 'image', 'order', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la noticia'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Extracto o resumen'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Contenido completo de la noticia'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pdf_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'show_pdf_inline': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'social_media_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.instagram.com/p/...'}),
        }

class MunicipalChronicleForm(forms.ModelForm):
    class Meta:
        model = MunicipalChronicle
        fields = ['title', 'content', 'image', 'publication_date', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la crónica'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Contenido detallado'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'publication_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Deportes, Economía, Promulgaciones'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.slug = slugify(instance.name)
        if commit:
            instance.save()
        return instance