from django.contrib import admin
from .models import Councilor, News, Carousel, AboutUs

@admin.register(Councilor)
class CouncilorAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    ordering = ('order',)

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'is_active')
    list_filter = ('is_active', 'publication_date')
    search_fields = ('title', 'description')
    ordering = ('-publication_date',)

@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)
    ordering = ('order',)

@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)