from django import forms
from django.utils.text import slugify
from .models import HomeCarouselNews, Category, Chronicle  

class HomeCarouselNewsForm(forms.ModelForm):
    class Meta:
        model = HomeCarouselNews
        fields = ['title', 'summary', 'content', 'category', 'image', 'order', 'is_active', 'pdf_file', 'show_pdf_inline', 'social_media_url']
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

class ChronicleForm(forms.ModelForm):
    class Meta:
        model = Chronicle  # Asegúrate de usar un único modelo de crónicas en models.py
        fields = ['title', 'summary', 'content', 'author', 'image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la crónica...'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Breve introducción o resumen...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Desarrollo completo de la crónica histórica...'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cronista o autor'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }