from django.contrib import admin
from .models import HomeCarouselNews, Category, Chronicle

# Registramos los modelos limpios en el panel de administración
@admin.register(HomeCarouselNews)
class HomeCarouselNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'summary')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Chronicle)
class ChronicleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_active', 'created_at')
    list_filter = ('is_active', 'author')
    search_fields = ('title', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}