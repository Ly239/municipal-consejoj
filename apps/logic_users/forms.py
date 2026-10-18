import re
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import Group

# Validaciones reutilizables
from common.validators import (
    validate_only_letters,
    validate_alphanumeric_name,
    validate_venezuelan_id,
    validate_venezuelan_phone,
    validate_unique_with_trash,
)

User = get_user_model()


# ============================================================
# 1. FORMULARIO DE LOGIN
# ============================================================
class LoginForm(forms.Form):
    """Formulario para iniciar sesión.

    Solo valida formato (los campos son required=True por defecto).
    La autenticación la hace la vista UserLoginView.
    """
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu nombre de usuario',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Tu Contraseña',
            'class': 'form-control'
        })
    )

    def clean(self):
        """Solo valida formato. La autenticación la hace la vista."""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if not username:
            self.add_error('username', "El nombre de usuario es obligatorio.")
        if not password:
            self.add_error('password', "La contraseña es obligatoria.")
        return cleaned_data


# ============================================================
# 2. FORMULARIO DE REGISTRO
# ============================================================
class RegisterForm(forms.Form):
    """
    Formulario para registrar nuevos usuarios (admin-only) (no se usa actualmente).

    Register en Sprint 2: solo falta configurar django-axes.
    Ver docs/PORQUE_AXES.md y docs/PLAN_REGISTER_Y_USUARIOS.md.
    """

    ROLE_CHOICES = [
        ('Viewer', 'Visualizador (solo lectura)'),
        ('Employee', 'Empleado (sube documentos)'),
        ('ContentManager', 'Gestor de contenido (Home)'),
        ('Administrator', 'Administrador (acceso total)'),
    ]

    # --- Datos de cuenta ---
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Define nombre de usuario',
            'class': 'form-control'
        })
    )

    # --- Datos personales ---
    first_name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu nombre',
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu apellido',
            'class': 'form-control'
        })
    )
    id_number = forms.CharField(
        label="Cédula",
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': 'V-12345678',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@gmail.com (opcional)',
            'class': 'form-control'
        })
    )
    phone = forms.CharField(
        label="Teléfono",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '0414-1234567 (opcional)',
            'class': 'form-control'
        })
    )
    address = forms.CharField(
        label="Dirección",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Dirección (opcional)',
            'class': 'form-control'
        })
    )

    # --- Rol ---
    rol = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='Viewer',
        label='Rol del usuario',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # --- Contraseñas ---
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Introduce tu Contraseña',
            'class': 'form-control'
        })
    )
    password_confirm = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repite tu Contraseña',
            'class': 'form-control'
        })
    )

    # ============================================================
    # VALIDACIONES (usando common/validators.py)
    # ============================================================

    def clean_first_name(self):
        return validate_only_letters(self.cleaned_data.get('first_name'), "El nombre")

    def clean_last_name(self):
        return validate_only_letters(self.cleaned_data.get('last_name'), "El apellido")

    def clean_username(self):
        """Formato + unicidad con papelera. Sin instance (RegisterForm es Form plano)."""
        username = self.cleaned_data.get('username')
        if not username:
            return username
        validate_alphanumeric_name(username, "El nombre de usuario")
        validate_unique_with_trash(User, 'username', username)
        return username

    def clean_id_number(self):
        """Cédula + unicidad con papelera."""
        id_number = self.cleaned_data.get('id_number')
        if not id_number:
            return id_number
        validate_venezuelan_id(id_number)
        validate_unique_with_trash(User, 'id_number', id_number)
        return id_number

    def clean_phone(self):
        """Teléfono + unicidad con papelera (opcional)."""
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        validate_venezuelan_phone(phone)
        validate_unique_with_trash(User, 'phone', phone)
        return phone

    def clean_email(self):
        """Unicidad con papelera (opcional)."""
        email = self.cleaned_data.get('email')
        if not email:
            return email
        validate_unique_with_trash(User, 'email', email)
        return email

    def clean_password(self):
        """Fortaleza de contraseña (mismo patrón que UserProfileForm)."""
        password = self.cleaned_data.get('password')
        if not password:
            return password

        if len(password) < 8 or len(password) > 15:
            raise forms.ValidationError("La contraseña debe tener entre 8 y 15 caracteres.")
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        if not re.search(r'\d', password):
            raise forms.ValidationError("La contraseña debe contener al menos un número.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError(
                "La contraseña debe contener al menos un carácter especial (ej: !@#$%^&*)."
            )
        return password

    def clean_rol(self):
        """Valida que el grupo exista en BD."""
        rol = self.cleaned_data.get('rol')
        if rol and not Group.objects.filter(name=rol).exists():
            raise forms.ValidationError(
                f"El rol '{rol}' no existe en el sistema. "
                "Ejecutá 'python manage.py seed_roles' primero."
            )
        return rol

    def clean(self):
        """Valida que las contraseñas coincidan."""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        """
        Crea el usuario en BD y le asigna el grupo (rol).
        Register admin-only — siempre crea, nunca edita.
        """
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data.get('email') or None,
            password=self.cleaned_data['password'],
        )
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.id_number = self.cleaned_data['id_number']
        user.phone = self.cleaned_data.get('phone') or None
        user.address = self.cleaned_data.get('address') or None
        if commit:
            user.save()
            group = Group.objects.get(name=self.cleaned_data['rol'])
            user.groups.add(group)
        return user


# ============================================================
# 3. FORMULARIO DE CAMBIO DE USUARIO (para el admin)
# ============================================================
class CustomUserChangeForm(UserChangeForm):
    """Formulario para editar usuarios en el admin de Django."""
    class Meta:
        model = User
        fields = "__all__"


# ============================================================
# 4. FORMULARIO DE PERFIL
# ============================================================
class UserProfileForm(forms.ModelForm):
    """Formulario para que el usuario edite su perfil y cambie su contraseña."""
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Requerida para cambiar contraseña'
        }),
        required=False
    )
    password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar en blanco si no cambia'
        }),
        required=False
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la nueva contraseña'
        }),
        required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'id_number', 'phone', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # ============================================================
    # VALIDACIONES (usando common/validators.py)
    # ============================================================

    def clean_first_name(self):
        return validate_only_letters(self.cleaned_data.get('first_name'), "El nombre")

    def clean_last_name(self):
        return validate_only_letters(self.cleaned_data.get('last_name'), "El apellido")

    def clean_username(self):
        """Formato + unicidad con papelera. Con instance (ModelForm)."""
        username = self.cleaned_data.get('username')
        if not username:
            return username
        validate_alphanumeric_name(username, "El nombre de usuario")
        validate_unique_with_trash(
            User, 'username', username,
            instance=self.instance, exclude_pk=True
        )
        return username

    def clean_id_number(self):
        """Cédula + unicidad con papelera."""
        id_number = self.cleaned_data.get('id_number')
        if not id_number:
            return id_number
        validate_venezuelan_id(id_number)
        validate_unique_with_trash(
            User, 'id_number', id_number,
            instance=self.instance, exclude_pk=True
        )
        return id_number

    def clean_phone(self):
        """Teléfono + unicidad con papelera."""
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        validate_venezuelan_phone(phone)
        validate_unique_with_trash(
            User, 'phone', phone,
            instance=self.instance, exclude_pk=True
        )
        return phone

    def clean_email(self):
        """Unicidad con papelera."""
        email = self.cleaned_data.get('email')
        if not email:
            return email
        validate_unique_with_trash(
            User, 'email', email,
            instance=self.instance, exclude_pk=True
        )
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not password1:
            return password1

        if len(password1) < 8 or len(password1) > 15:
            raise forms.ValidationError("La contraseña debe tener entre 8 y 15 caracteres.")
        if not re.search(r'[A-Z]', password1):
            raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        if not re.search(r'\d', password1):
            raise forms.ValidationError("La contraseña debe contener al menos un número.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise forms.ValidationError(
                "La contraseña debe contener al menos un carácter especial (ej: !@#$%^&*)."
            )
        return password1

    def clean(self):
        """Validaciones cruzadas (sin try/except — usa add_error)."""
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        user = self.instance

        if password1 or password2:
            if not old_password:
                self.add_error('old_password', "Debe ingresar su contraseña actual para cambiarla.")
            elif not user.check_password(old_password):
                self.add_error('old_password', "Contraseña actual incorrecta.")
            elif password1 != password2:
                self.add_error('password2', "Las contraseñas nuevas no coinciden.")
            elif password1 == old_password:
                self.add_error('password1', "La nueva contraseña debe ser diferente a la actual.")
            else:
                cleaned_data['new_password'] = password1
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('new_password'):
            user.set_password(self.cleaned_data['new_password'])
        if commit:
            user.save()
        return user
