"""
Copyright [2026] [Proyecto universitario]

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

from django.contrib import admin
from .models import (
    HomeContent,
    News,
    Chronicle,
    Councilor,
    Carousel,
    AboutUs,
    Category,
    Commission,
    Legislature,
    BoardMember,

)


@admin.register(HomeContent)
class HomeContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'status', 'publication_date', 'order', 'is_active')
    list_filter = ('content_type', 'status', 'is_active', 'category')
    search_fields = ('title', 'summary', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_active', 'created_at', 'order')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Chronicle)
class ChronicleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'publication_date', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('title', 'author', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Councilor)
class CouncilorAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'order', 'is_active')
    search_fields = ('title', 'author')


@admin.register(Carousel)
class CarouselAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('number', 'name')
    search_fields = ('name', 'description')




@admin.register(Legislature)
class LegislatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'order', 'status', 'is_active', 'publication_date')
    list_filter = ('status', 'is_active')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}

    def get_queryset(self, request):
        return super().get_queryset(request).filter(content_type='LEGISLATURE')

    def save_model(self, request, obj, form, change):
        obj.content_type = 'LEGISLATURE'
        if not change and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BoardMember)
class BoardMemberAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'order', 'status', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('title', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}

    def get_queryset(self, request):
        return super().get_queryset(request).filter(content_type='BOARD')

    def save_model(self, request, obj, form, change):
        obj.content_type = 'BOARD'
        if not change and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)