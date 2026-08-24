"""
Funciones de validación reutilizables en todo el proyecto.
"""
import re
from django.core.exceptions import ValidationError


def validate_only_letters(value, field_name="Field"):
    """Valida que un string contenga solo letras, espacios, tildes y la letra ñ/Ñ."""
    if value and not re.match(r'^[A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+$', value):
        raise ValidationError(f"{field_name} solo puede contener letras, espacios y acentos.")
    return value


def validate_alphanumeric_name(value, field_name="Nombre"):
    """Valida nombres alfanuméricos con guión bajo, entre 4 y 20 caracteres."""
    if not value:
        return value
    value = value.strip()
    if len(value) < 4 or len(value) > 20:
        raise ValidationError(f"{field_name} debe tener entre 4 y 20 caracteres.")
    if not re.match(r'^[A-Za-z0-9_]+$', value):
        raise ValidationError(f"{field_name} solo puede contener letras, números y guión bajo (_).")
    if not any(c.isalpha() for c in value):
        raise ValidationError(f"{field_name} debe contener al menos una letra.")
    if all(c == value[0] for c in value) and value[0].isalpha():
        raise ValidationError(f"{field_name} no puede consistir en una sola letra repetida.")
    return value


def validate_venezuelan_id(id_number):
    """Valida cédula venezolana: 8 dígitos, no todos iguales."""
    if not id_number:
        return id_number
    id_number = id_number.strip()
    if not re.match(r'^\d{8}$', id_number):
        raise ValidationError("La cédula debe tener exactamente 8 dígitos (solo números).")
    if id_number == id_number[0] * 8:
        raise ValidationError("La cédula no puede tener todos los dígitos iguales.")
    return id_number


def validate_venezuelan_phone(phone):
    """Valida teléfono regional: 11 dígitos, código válido, resto no repetido."""
    if not phone:
        return phone
    phone_clean = re.sub(r'\D', '', phone)
    if not re.match(r'^\d{11}$', phone_clean):
        raise ValidationError("El teléfono debe tener 11 dígitos (ejemplo: 04121234567).")
    codigos_validos = ['0412', '0414', '0416', '0424', '0426', '0422']
    if phone_clean[:4] not in codigos_validos:
        raise ValidationError("El código de operadora no es válido para esta región.")
    resto = phone_clean[4:]
    if resto == resto[0] * 7:
        raise ValidationError("El número de teléfono no puede tener todos los dígitos iguales después del código.")
    return phone_clean



def validate_unique_with_trash(model, field_name, value, instance=None, exclude_pk=False):
    """
    Valida que el valor de un campo sea único, considerando también registros en papelera.
    - model: el modelo (ej: Gazette, Document, User)
    - field_name: el nombre del campo (ej: 'number', 'id_number')
    - value: el valor a validar
    - instance: la instancia actual (para excluirla en edición)
    - exclude_pk: si es True, excluye la instancia actual por su pk
    """
    if not value:
        return

    # Construir el filtro
    filters = {field_name: value}
    qs = model.all_objects.filter(**filters)

    # Excluir la instancia actual si estamos editando
    if instance and exclude_pk:
        qs = qs.exclude(pk=instance.pk)

    existing = qs.first()
    if existing:
        if existing.is_deleted:
            raise ValidationError(
                f"Ya existe un registro con este {field_name} en la papelera. "
                "Restáuralo o elimínalo definitivamente."
            )
        else:
            raise ValidationError(f"Ya existe un registro con este {field_name}.")