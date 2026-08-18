from django.db import models
from django.contrib.auth.models import AbstractUser
from common.models import TimestampedMixin, SoftDeleteMixin


class User(AbstractUser, TimestampedMixin, SoftDeleteMixin):
    # Modelo de usuario personalizado.
    
    # Campos adicionales
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

    # Redefinimos estos campos para darles verbose_name en español
    is_staff = models.BooleanField(
        default=False,
        verbose_name="¿Es miembro del staff? (acceso al admin de Django)"
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="¿Es superusuario? (todos los permisos)"
    )
    _is_active = models.BooleanField(
        default=True,
        verbose_name="Activo (cuenta habilitada)"
    )

    # Redefinimos campos heredados para verbose_name en español
    first_name = models.CharField(max_length=150, verbose_name="Nombre(s)")
    last_name = models.CharField(max_length=150, verbose_name="Apellido(s)")
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nombre de usuario"
    )

    # Configuración de autenticación
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'id_number']

    class Meta:
        db_table = "users"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} ({self.email})"

    @property
    def is_active(self):
        """
        Un usuario puede iniciar sesión solo si:
        - No está borrado suavemente (deleted_at is None)
        - Y la cuenta está activa (_is_active = True)
        """
        return self.deleted_at is None and self._is_active

    def delete(self, using=None, keep_parents=False):
        """
        Soft delete: desactiva la cuenta y la marca como borrada.
        """
        self._is_active = False
        super().delete(using=using, keep_parents=parents)

