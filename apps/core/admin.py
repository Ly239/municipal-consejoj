from django.contrib import admin
from .models import HomeCarouselNews, MunicipalChronicle

@admin.register(HomeCarouselNews)
class HomeCarouselNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')

@admin.register(MunicipalChronicle)
class MunicipalChronicleAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'is_published')
    list_editable = ('is_published',)