from django import template

# Registramos el archivo dentro de la librería de plantillas de Django
register = template.Library()

@register.filter(name='get_attribute')
def get_attribute(value, arg):
    """
    Obtiene dinámicamente el valor de un campo de cualquier objeto.
    Uso en HTML: {{ objeto|get_attribute:"nombre_del_campo" }}
    """
    # Si el objeto tiene el atributo indicado en 'arg'
    if hasattr(value, str(arg)):
        attr = getattr(value, str(arg))
        # Si es un método o función (ej. un get_status_display), lo ejecuta
        if callable(attr):
            return attr()
        return attr
    # Si el valor resulta ser un diccionario
    elif isinstance(value, dict):
        return value.get(arg, None)
    return ''