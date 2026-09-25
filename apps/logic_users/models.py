from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from common.models import TimestampedMixin, SoftDeleteMixin


# ============================================================
# MANAGERS PERSONALIZADOS
# ============================================================
class UserManager(BaseUserManager):
    """
    Manager por defecto: solo devuelve usuarios NO borrados (deleted_at is None).
    Se usa para queries normales (login, listados activos, validaciones de unicidad).
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Crea un usuario común."""
        if not username:
            raise ValueError("El nombre de usuario es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Crea un superusuario."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")
        return self.create_user(username, email, password, **extra_fields)


class AllUserManager(BaseUserManager):
    """
    Manager que devuelve TODOS los usuarios, incluidos los borrados.
    Se usa para la papelera universal (listar, restaurar, eliminar permanentemente).
    """

    def get_queryset(self):
        return super().get_queryset()


# ============================================================
# MODELO DE USUARIO PERSONALIZADO
# ============================================================
class User(AbstractUser, TimestampedMixin, SoftDeleteMixin):
    """
    Modelo de usuario personalizado.
    Hereda de:
    - AbstractUser (Django): username, password, email, is_active, is_staff, etc.
    - TimestampedMixin (common): created_at, updated_at.
    - SoftDeleteMixin (common): deleted_at, soft_delete(), restore(), hard_delete().

    Integrado a la papelera universal (include_in_trash = True).
    """

    # --- Managers ---
    # objects: solo activos (no borrados). Es el default del admin y de las queries normales.
    # all_objects: todos, incluidos borrados. Se usa en la papelera.
    objects = UserManager()
    all_objects = AllUserManager()

    # --- Configuración de papelera ---
    include_in_trash = True

    # --- Campos adicionales ---
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo electrónico"
    )
    id_number = models.CharField(
        unique=True,
        max_length=15,
        verbose_name="Cédula",
        help_text="Número de identificación (V-12345678)"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Teléfono"
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Dirección"
    )

    # --- Configuración de autenticación ---
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'id_number']

    class Meta:
        db_table = "users"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} ({self.email})"

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete: desactiva la cuenta y la marca como borrada.
        Al restaurar, el admin debe reactivar manualmente is_active.

        corregido typo 'parents' -> 'keep_parents'.
        """
        self.is_active = False
        super().delete(using=using, keep_parents=keep_parents)