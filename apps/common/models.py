# Modelos base y mixins comunes para todo el proyecto.
from django.db import models
from django.utils import timezone


# ------------------------------------------------------------------------
# 1. MIXIN DE TIMESTAMP (fechas automáticas)
# ------------------------------------------------------------------------
class TimestampedMixin(models.Model):
    """Mixin que añade campos created_at y updated_at con actualización automática."""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Sobrescribe save para asegurar que updated_at siempre se actualice."""
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


# ------------------------------------------------------------------------
# 2. MIXIN DE BORRADO SUAVE (soft delete)
# ------------------------------------------------------------------------
class SoftDeleteMixin(models.Model):
    """Mixin que añade funcionalidad de borrado suave (campo deleted_at)."""
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Borrado')

    class Meta:
        abstract = True

    def soft_delete(self):
        """Marca el registro como borrado (borrado suave)."""
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restaura un registro borrado suavemente."""
        self.deleted_at = None
        self.save()

    def delete(self, using=None, keep_parents=False):
        """Borrado suave: marca la fecha en lugar de borrar de la BD."""
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """Borrado físico real (permanente). Usar con precaución."""
        super().delete(using=using, keep_parents=keep_parents)

    @property
    def is_deleted(self):
        """Verifica si el registro está borrado suavemente."""
        return self.deleted_at is not None

    @classmethod
    def get_softdelete_permission_name(cls):
        """Retorna el nombre del permiso para borrado suave."""
        return f"soft_delete_{cls._meta.model_name}"

    @classmethod
    def get_restore_permission_name(cls):
        """Retorna el nombre del permiso para restaurar."""
        return f"restore_{cls._meta.model_name}"


class ActiveManager(models.Manager):
    """Manager que devuelve solo objetos NO borrados suavemente (deleted_at is None)."""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


# ------------------------------------------------------------------------
# 3. MODELO BASE (combina ambos mixins)
# ------------------------------------------------------------------------
class BaseModel(TimestampedMixin, SoftDeleteMixin):
    """
    Modelo abstracto base que combina:
    - TimestampedMixin (created_at, updated_at)
    - SoftDeleteMixin (deleted_at, soft_delete, restore)
    """
    include_in_trash = True  # Si es False, el modelo no aparece en la papelera universal

    class Meta:
        abstract = True

    # Manager por defecto: solo objetos activos (no borrados)
    objects = ActiveManager()
    # Manager que incluye todos (incluso borrados)
    all_objects = models.Manager()