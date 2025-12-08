from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Añade la clase CSS especificada a un campo de formulario de Django.
    Uso: {{ field|add_class:'form-control' }}
    """
    return value.as_widget(attrs={'class': arg})

@register.filter(name='replace')
def replace(value, arg):
    """
    Filtro personalizado para reemplazar una subcadena por otra.
    Uso: {{ value|replace:'antiguo,nuevo' }}
    """
    if isinstance(value, str) and isinstance(arg, str):
        # El argumento debe ser 'antiguo,nuevo'
        parts = arg.split(',')
        if len(parts) == 2:
            old, new = parts
            return value.replace(old, new)
    return value