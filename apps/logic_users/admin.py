from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from common.mixins import SoftDeleteAdminMixin
from .forms import CustomUserChangeForm

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(SoftDeleteAdminMixin, BaseUserAdmin):
   
    form = CustomUserChangeForm
    model = User

    # Acciones disponibles (soft delete y restore)
    actions = ['action_soft_delete', 'action_restore']  # No se incluye hard delete

    # Columnas en la lista de usuarios
    list_display = (
        'id', 'username', 'email', 'id_number', 'phone',
        '_is_active', 'is_staff', 'is_superuser',
        'created_at', 'updated_at', 'deleted_at', 'estado_usuario'
    )
    list_display_links = ('id', 'username')
    search_fields = ('username', 'email', 'id_number', 'phone')
    
    # Filtros: el mixin ya añade el filtro de borrado, agregamos los nuestros
    list_filter = SoftDeleteAdminMixin.list_filter + [
        '_is_active', 'is_staff', 'is_superuser'
    ]
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at', 'deleted_at')
    list_per_page = 20

    # Secciones para edición de usuario (formulario de edición)
    fieldsets = (
        ('Credenciales', {'fields': ('username', 'password')}),
        ('Información personal', {
            'fields': ('first_name', 'last_name', 'email', 'id_number', 'phone', 'address')
        }),
        ('Permisos', {
            'fields': ('_is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at', 'deleted_at')
        }),
    )

    # Campos para creación rápida (add user)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'id_number', 'phone', 'address',
                'password1', 'password2',
                '_is_active', 'is_staff', 'is_superuser'
            ),
        }),
    )

    # ============================================================
    # MÉTODOS PERSONALIZADOS PARA EL ADMIN
    # ============================================================
    @admin.display(description="Estado", ordering='_is_active')
    def estado_usuario(self, obj):
        """
        Muestra el estado del usuario en formato legible.
        """
        if obj.deleted_at:
            return "🗑️ Eliminado"
        elif obj._is_active:
            return "✅ Activo"
        else:
            return "⛔ Inactivo"
            
            
    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.is_superuser:
            # Añadir acción de hard delete solo para superusuarios
            actions['hard_delete_selected'] = (
                self.hard_delete_selected,
                'hard_delete_selected',
                'Eliminar permanentemente (SOLO SUPERUSUARIO)'
            )
        return actions

    def hard_delete_selected(self, request, queryset):
        """Elimina permanentemente los usuarios seleccionados."""
        count = queryset.count()
        for user in queryset:
            user.hard_delete()
        self.message_user(request, f"{count} usuario(s) eliminados permanentemente.")
        hard_delete_selected.short_description = "Eliminar permanentemente (SOLO SUPERUSUARIO)"
