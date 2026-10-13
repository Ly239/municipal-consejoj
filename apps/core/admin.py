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
    BaseContent,
    News,
    Chronicle,
    Councilor,
    AboutUs,
    Activity,
    Announcement,
    Consultation,
    Event,
    Downloadable,
    Category,
    Commission,
    Legislature,
    Legislator,
    CommissionMember,
)


# ==============================================================================
# 1. INLINES (Edición en línea para relaciones)
# ==============================================================================

class CommissionMemberInline(admin.TabularInline):
    model = CommissionMember
    extra = 1


class LegislatorInline(admin.TabularInline):
    model = Legislator
    extra = 1


# ==============================================================================
# 2. CONTENIDO PRINCIPAL Y PROXIES
# ==============================================================================

@admin.register(BaseContent)
class BaseContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'status', 'publication_date', 'order', 'is_active')
    list_filter = ('content_type', 'status', 'is_active', 'category')
    search_fields = ('title', 'summary', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'publication_date', 'is_active', 'order')
    list_filter = ('status', 'is_active', 'category')
    search_fields = ('title', 'summary', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Chronicle)
class ChronicleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'publication_date', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('title', 'author', 'summary', 'content')
    prepopulated_fields = {'slug': ('title',)}

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Councilor)
class CouncilorAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'order', 'is_active')
    search_fields = ('title', 'author', 'summary')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'is_active')
    search_fields = ('title', 'summary')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'publication_date', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'publication_date', 'is_active')
    search_fields = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'status', 'is_active')
    search_fields = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'status', 'is_active')
    search_fields = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Downloadable)
class DownloadableAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_year', 'status', 'is_active')
    search_fields = ('title', 'summary')
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(description='Año')
    def get_year(self, obj):
        return obj.publication_date.year if obj.publication_date else '-'


# ==============================================================================
# 3. MODELOS AUXILIARES
# ==============================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'emoji')
    search_fields = ('name', 'description')
    inlines = [CommissionMemberInline]


@admin.register(Legislature)
class LegislatureAdmin(admin.ModelAdmin):
    list_display = ('roman_id', 'years', 'mayor', 'order')
    search_fields = ('roman_id', 'years', 'mayor')
    inlines = [LegislatorInline]