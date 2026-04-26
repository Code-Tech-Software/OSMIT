from django.urls import path, include
from rest_framework.routers import DefaultRouter
from appMovil import views
from .views import *



router = DefaultRouter()
router.register(r'roles', RolViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'categorias', CategoriaProductoViewSet)
router.register(r'presentaciones', PresentacionProductoTerminadoViewSet)
router.register(r'productos', ProductoTerminadoViewSet)
router.register(r'variaciones', ProductoVariacionViewSet)
router.register(r'vehiculos', VehiculoViewSet)
router.register(r'rutas', RutaViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'cliente-dias', ClienteDiasVisitaViewSet)

router.register(r'mini-bodegas', MiniBodegaViewSet)
router.register(r'mini-bodega-detalles', MiniBodegaDetalleViewSet)

router.register(r'ventas', VentaViewSet)
router.register(r'venta-detalles', VentaDetalleViewSet)

router.register(r'pedidos-reabastecimiento', PedidoReabastecimientoViewSet)
router.register(r'pedido-reabastecimiento-detalles', PedidoReabastecimientoDetalleViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('mini-bodega/cerrar/', cerrar_mini_bodega),
    path('reabastecimiento/crear/', crear_reabastecimiento),
    path('reabastecimiento/sincronizar/', sincronizar_reabastecimiento),

    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedidos/<int:pedido_id>/procesar/', views.procesar_reabastecimiento, name='procesar_reabastecimiento'),
]
