# miapp/templatetags/rol_tags.py
from django import template

register = template.Library()

@register.filter
def has_role(user, roles_csv):
    """
    Devuelve True si el usuario está autenticado y su rol
    está en la lista (roles_csv es una cadena 'Rol1,Rol2,...').
    Ejemplo de uso:
       {% if user|has_role:"Admin,Editor" %}
    """
    # Asegurarse de que hay un usuario y tiene atributo rol
    if not getattr(user, 'is_authenticated', False):
        return False
    rol = getattr(user, 'rol', None)
    if not rol or not rol.nombre:
        return False

    # Convertir la cadena CSV en lista y comparar
    allowed = [r.strip() for r in roles_csv.split(',')]
    return rol.nombre in allowed
