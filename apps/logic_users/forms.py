import re
from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UserChangeForm

# Importamos las funciones de validación desde common.validators
from common.validators import (
    validate_only_letters,
    validate_alphanumeric_name,
    validate_venezuelan_id,
    validate_venezuelan_phone
)

User = get_user_model()


# ------------------------------------------------------------
# 1. FORMULARIO DE LOGIN
# ------------------------------------------------------------
class LoginForm(forms.Form):
    """Formulario para iniciar sesión."""
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
        """Autentica al usuario con las credenciales proporcionadas."""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Usuario o contraseña incorrectos.")
            if not user.is_active:
                raise forms.ValidationError("Esta cuenta está desactivada o ha sido eliminada.")
            cleaned_data['user'] = user
        return cleaned_data


# ------------------------------------------------------------
# 2. FORMULARIO DE REGISTRO (opcional, para uso futuro)
# ------------------------------------------------------------
class RegisterForm(forms.Form):
    """Formulario para registrar nuevos usuarios (no se usa actualmente)."""
    username = forms.CharField(
        label="Nombre de Usuario",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Define nombre de usuario',
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@gmail.com',
            'class': 'form-control'
        })
    )
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

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Las contraseñas no coinciden.")
        return cleaned_data


# ------------------------------------------------------------
# 3. FORMULARIO DE CAMBIO DE USUARIO (para el admin)
# ------------------------------------------------------------
class CustomUserChangeForm(UserChangeForm):
    """Formulario para editar usuarios en el admin de Django."""
    class Meta:
        model = User
        fields = "__all__"


# ------------------------------------------------------------
# 4. FORMULARIO DE PERFIL (para que el usuario edite sus datos)
# ------------------------------------------------------------
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

    # ========== VALIDACIONES ==========
    def clean_first_name(self):
        return validate_only_letters(self.cleaned_data.get('first_name'), "El nombre")

    def clean_last_name(self):
        return validate_only_letters(self.cleaned_data.get('last_name'), "El apellido")

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if len(username) < 4 or len(username) > 20:
                raise forms.ValidationError("El nombre de usuario debe tener entre 4 y 20 caracteres.")
            if not re.match(r'^[A-Za-z0-9_]+$', username):
                raise forms.ValidationError(
                    "El nombre de usuario solo puede contener letras, números y guión bajo (_)."
                )
            if not any(c.isalpha() for c in username):
                raise forms.ValidationError("El nombre de usuario debe contener al menos una letra.")
            if all(c == username[0] for c in username) and username[0].isalpha():
                raise forms.ValidationError("El nombre de usuario no puede consistir en una sola letra repetida.")
        return username

    def clean_id_number(self):
        return validate_venezuelan_id(self.cleaned_data.get('id_number'))

    def clean_phone(self):
        return validate_venezuelan_phone(self.cleaned_data.get('phone'))

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
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
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        user = self.instance

        # Si se proporcionó una nueva contraseña, validar
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
                cleaned_data['new_password'] = password1  # Guardamos para usar en save()
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('new_password'):
            user.set_password(self.cleaned_data['new_password'])
        if commit:
            user.save()
        return user