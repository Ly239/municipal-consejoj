"""
Funciones de validación reutilizables en todo el proyecto.
"""
import re
from datetime import date
from django.core.exceptions import ValidationError


def validate_only_letters(value, field_name="Field"):
    """Valida que un string contenga solo letras, espacios, tildes y la letra ñ/Ñ."""
    if value and not re.match(r'^[A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+$', value):
        raise ValidationError(f"{field_name} solo puede contener letras, espacios y acentos.")
    return value


def validate_alphanumeric_name(value, field_name="Nombre"):
    """
    Valida nombres alfanuméricos con guión bajo, entre 4 y 20 caracteres.
    Rechaza strings que sean una sola letra repetida (ej: 'aaaa').
    """
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
    """
    Valida cédula venezolana: 8 dígitos, no todos ceros.
    Nota: NO se rechaza 'todos los dígitos iguales' (ej: 11111111)
    porque las cédulas se emiten secuencialmente y podrían existir.
    """
    if not id_number:
        return id_number
    id_number = id_number.strip()
    if not re.match(r'^\d{8}$', id_number):
        raise ValidationError("La cédula debe tener exactamente 8 dígitos (solo números).")
    if id_number == '00000000':
        raise ValidationError("La cédula no puede ser 00000000.")
    return id_number


def validate_venezuelan_phone(phone):
    """
    Valida teléfono regional: 11 dígitos, código de operadora válido.
    Nota: solo se rechaza 'todos ceros' después del código (número
    imposible en la práctica). Otros casos se aceptan.
    """
    if not phone:
        return phone
    phone_clean = re.sub(r'\D', '', phone)
    if not re.match(r'^\d{11}$', phone_clean):
        raise ValidationError("El teléfono debe tener 11 dígitos (ejemplo: 04121234567).")
    codigos_validos = ['0412', '0414', '0416', '0424', '0426', '0422']
    if phone_clean[:4] not in codigos_validos:
        raise ValidationError("El código de operadora no es válido para esta región.")
    resto = phone_clean[4:]
    if resto == '0' * 7:
        raise ValidationError("El número de teléfono no puede ser todo ceros después del código.")
    return phone_clean


def validate_number_range(value, min_value=1, max_value=None, field_name="Número"):
    """
    Valida un número dentro de un rango.

    Parámetros:
    - value: el número a validar.
    - min_value: mínimo permitido (por defecto 1).
    - max_value: máximo permitido (opcional; si es None, no valida superior).
    - field_name: nombre del campo para el mensaje de error.
    """
    if value is None:
        return value
    if value < min_value:
        raise ValidationError(f"{field_name} debe ser mayor o igual a {min_value}.")
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name} no puede superar {max_value}.")
    return value


def validate_future_date(value, field_name="Fecha"):
    """
    Valida que la fecha no sea futura.
    Coherente con la política del cliente: no se permiten fechas futuras.
    """
    if value and value > date.today():
        raise ValidationError(f"{field_name} no puede ser una fecha futura.")
    return value


def validate_year(value, field_name="Año"):
    """
    Valida que el año esté entre 1900 y el año actual.
    No permite años futuros: coherente con validate_future_date y con la
    política del cliente (no se crean gacetas huérfanas sin documentos).
    """
    current_year = date.today().year
    if value and (value < 1900 or value > current_year):
        raise ValidationError(f"{field_name} debe estar entre 1900 y {current_year}.")
    return value


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
