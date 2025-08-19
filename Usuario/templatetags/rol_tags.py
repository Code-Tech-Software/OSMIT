# miapp/templatetags/rol_tags.py
from django import template

register = template.Library()

@register.filter
def has_role(user, roles_csv):

    # Asegurarse de que hay un usuario y tiene atributo rol
    if not getattr(user, 'is_authenticated', False):
        return False
    rol = getattr(user, 'rol', None)
    if not rol or not rol.nombre:
        return False

    # Convertir la cadena CSV en lista y comparar
    allowed = [r.strip() for r in roles_csv.split(',')]
    return rol.nombre in allowed
