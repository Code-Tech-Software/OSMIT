from django.db import transaction
from django.db.models import F
from ..models import ProductoGranel

def obtener_siguiente_numero_lote(producto_id):
    with transaction.atomic():
        producto = ProductoGranel.objects.select_for_update().get(pk=producto_id)
        siguiente = (producto.ultimo_numero_lote % 99) + 1
        ProductoGranel.objects.filter(pk=producto_id).update(ultimo_numero_lote=siguiente)
        return siguiente