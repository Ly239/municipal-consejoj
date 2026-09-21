"""
Configuración del panel de administración para la app documents.
"""
from django.contrib import admin
from django import forms
from common.mixins import SoftDeleteAdminMixin
from .models import DocumentType, IssuingEntity, Gazette, Document


# ==================================================
# 1. ADMIN PARA TABLAS SEEDER (sin soft delete)
# ==================================================

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    """Administración de tipos de documento."""
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 20


@admin.register(IssuingEntity)
class IssuingEntityAdmin(admin.ModelAdmin):
    """Administración de entes emisores."""
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)
    ordering = ('name',)
    list_per_page = 20


# ==================================================
# 2. ADMIN PARA MODELOS CON SOFT DELETE
# ==================================================

@admin.register(Gazette)
class GazetteAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """Administración de Gacetas."""
    list_display = (
        'id', 'number', 'year', 'description_short', 
        'has_documents', 'created_at', 'deleted_at'
    )
    list_filter = SoftDeleteAdminMixin.list_filter + ['year']
    search_fields = ('number', 'year', 'description')
    ordering = ('-year', '-number')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    list_per_page = 20

    def description_short(self, obj):
        """Muestra los primeros 50 caracteres de la descripción."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = "Descripción (resumen)"

    def has_documents(self, obj):
        """Indica si la gaceta tiene documentos asociados."""
        return obj.documents.exists()
    has_documents.boolean = True
    has_documents.short_description = "¿Tiene documentos?"


@admin.register(Document)
class DocumentAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'id', 'document_type', 'number', 'gazette_year', 'title_short',
        'issuing_entity', 'is_approved', 'submitted_by', 
        'emission_date', 'deleted_at'
    )
    list_filter = SoftDeleteAdminMixin.list_filter + [
        'document_type', 'issuing_entity', 'is_approved',
        'emission_date'
    ]
    search_fields = (...)
    ordering = ('-emission_date',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at', 'publication_date')
    list_per_page = 20
    date_hierarchy = 'emission_date'

    fieldsets = (
        ('Información principal', {
            'fields': (
                'gazette', 'document_type', 'issuing_entity',
                'number', 'title', 'description', 'is_approved'
            )
        }),
        ('Fechas', {
            'fields': ('emission_date', 'publication_date')
        }),
        ('Archivos adjuntos', {
            'fields': ('pdf_file', 'image'),
            'classes': ('collapse',)
        }),
        ('Otros datos', {
            'fields': ('other_entity_description',),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    # ================================================================
    # Asignar automáticamente submitted_by al crear
    # Motivo: submitted_by es NOT NULL. En las vistas ya lo asignamos,
    # pero el admin no lo hace por defecto → IntegrityError al crear.
    # ================================================================
    def save_model(self, request, obj, form, change):
        """
        Asigna el usuario logueado a submitted_by solo en creación.
        En edición, mantiene el valor original (no lo pisa).
        """
        if not change:  # change=False significa "creación"
            obj.submitted_by = request.user
        super().save_model(request, obj, form, change)

    def title_short(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_short.short_description = "Título (resumen)"

    def gazette_year(self, obj):
        return obj.gazette.year
    gazette_year.short_description = "Año de Gaceta"
    gazette_year.admin_order_field = 'gazette__year'
