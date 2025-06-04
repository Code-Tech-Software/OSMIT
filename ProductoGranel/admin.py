from django.contrib import admin

from ProductoGranel.models import *

admin.site.register(CategoriaProducto)
admin.site.register(Proveedor)
admin.site.register(ProductoGranel)
admin.site.register(EntradaGranel)
admin.site.register(DetalleEntradaGranel)
admin.site.register(SalidaGranel)
admin.site.register(DetalleSalidaGranel)
admin.site.register(PedidoProduccion)
admin.site.register(DetallePedidoProduccion)
admin.site.register(DevolucionGranel)
admin.site.register(DetalleDevolucionGranel)
admin.site.register(Lote)
admin.site.register(CorteInventarioGranel)
admin.site.register(DetalleCorteInventarioGranel)