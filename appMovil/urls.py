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
router.register(r'abonos', AbonoViewSet)

router.register(r'ventas', VentaViewSet)
router.register(r'venta-detalles', VentaDetalleViewSet)

router.register(r'pedidos-reabastecimiento', PedidoReabastecimientoViewSet)
router.register(r'pedido-reabastecimiento-detalles', PedidoReabastecimientoDetalleViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('mini-bodega/cerrar/', cerrar_mini_bodega),
    path('reabastecimiento/crear/', crear_reabastecimiento),
    path('reabastecimiento/sincronizar/', sincronizar_reabastecimiento),

    path('pedidos/', views.lista_pedidos, name='lista_pedidos_reparto'),
    path('pedidos/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido_reparto'),
    path('pedidos/<int:pedido_id>/procesar/', views.procesar_reabastecimiento, name='procesar_reabastecimiento'),

    path('minibodegas/', views.minibodega_list, name='minibodega_lista'),

    # Ruta para el detalle (Llama a la función minibodega_detail pasando el pk)
    path('minibodegas/<int:pk>/', views.minibodega_detail, name='minibodega_detalle'),

    path('minibodegas/agregar/', views.agregar_minibodega, name='agregar_minibodega'),
    path('sync/ventas/', sync_ventas),
    path('sync/abonos/', sync_abonos),
    path('sync/devoluciones/', sync_devoluciones),
    path('movil/ventas/', get_ventas),
    path('movil/abonos/', get_abonos),
    path('movil/devoluciones/', get_devoluciones),

    path('ventas2/', ListaVentasView.as_view(), name='lista_ventas'),
    path('ventas2/<int:pk>/', DetalleVentaView.as_view(), name='detalle_venta'),

    # ---------------------------------------------------------------------------------------- CARGAR CSV
    path('cargar-clientes/', views.cargar_clientes_csv, name='cargar_clientes_csv'),
    path('cargar-productos/', views.cargar_productos_csv, name='cargar_productos'),
    path('minibodega/<int:pk>/abrir/', views.abrir_minibodega_manual, name='abrir_minibodega_manual'),
    path('minibodega/detalle/<int:detalle_pk>/regresar/', views.regresar_producto_bodega,
         name='regresar_producto_bodega'),

    path('devoluciones/', ListaDevolucionesView.as_view(), name='lista_devoluciones'),
    path('devoluciones/<int:pk>/', DetalleDevolucionView.as_view(), name='detalle_devolucion'),
]
