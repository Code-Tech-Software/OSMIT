from django.contrib import admin

from ProductoTerminado.models import *

admin.site.register(PresentacionProductoTerminado)
admin.site.register(ProductoTerminado)
admin.site.register(Vehiculo)
admin.site.register(Ruta)
admin.site.register(Cliente)
admin.site.register(ClienteDiasVisita)
admin.site.register(EntradaPTerminado)
admin.site.register(DetalleEntradaPTerminado)
admin.site.register(SalidaPTerminado)
admin.site.register(DetalleSalidaPTerminado)
admin.site.register(InventarioRuta)
admin.site.register(ProductoVariacion)
