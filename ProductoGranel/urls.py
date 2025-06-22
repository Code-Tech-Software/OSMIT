from django.urls import path
from . import views
from .views import recursos_humanos_json, rechazar_pedido_produccion

urlpatterns = [
    # ENTRADAS
    path('agregar/', views.agregar_producto_granel, name='agregar_producto_granel'),
    path('registrar/', views.registrar_entrada, name='registrar_entrada'),
    # SALIDAS
    path('salida/', views.registrar_salida, name='registrar_salida'),
    # PEDIDOS
    path('pedido/registrar/', views.registrar_pedido_produccion, name='registrar_pedido_produccion'),
    path('pedido/lista', views.lista_pedidos, name='lista_pedidos'),  # ESTAR ATENTO

    path('pedidos/aceptar/<int:pedido_id>/', views.aceptar_pedido_produccion, name='aceptar_pedido_produccion'),
    # -DEVOLUCIONES
    path('salidas/', views.lista_salidas, name='lista_salidas'),
    path('devolucion/salida/<int:salida_id>/registrar/', views.registrar_devolucion, name='registrar_devolucion'),
    # CORTES--------------------------
    path('corte/realizar/', views.realizar_corte, name='realizar_corte'),
    path('corte/lista/', views.lista_cortes, name='lista_cortes'),

    # en revision#
    path('corte/<int:corte_id>/ajustar/', views.ajustar_inventario, name='ajustar_inventario'),

    path('corte/<int:corte_id>/detalle/', views.detalle_corte, name='detalle_corte'),

    path('productos/', views.listar_productos_granel, name='listar_productos_granel'),
    path('productos/editar/<int:pk>/', views.editar_producto_granel, name='editar_producto_granel'),
    path('productos/eliminar/<int:pk>/', views.eliminar_producto_granel, name='eliminar_producto_granel'),

    # CATEGORIAS DE PRODUCTOS
    path('listaCategoria/', views.lista_categorias, name='lista_categorias'),
    path('crearCategoria/', views.crear_categoria, name='crear_categoria'),
    path('editarCategoria/<int:pk>/', views.editar_categoria, name='editar_categoria'),
    path('eliminarCategoria/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),

    # PROVEEDORES DE PRODUCTOS A GRANEL

    path('listaProveedor/', views.lista_proveedores, name='lista_proveedores'),
    path('crearProveedor/', views.crear_proveedor, name='crear_proveedor'),
    path('editaProveedor/<int:pk>/', views.editar_proveedor, name='editar_proveedor'),
    path('eliminarProveedor/<int:pk>/', views.eliminar_proveedor, name='eliminar_proveedor'),

    # DASBOAR
    path('api/entradas-salidas/', views.entradas_salidas_por_dia, name='entradas_salidas'),
    path('api/top-productos-salidas/', views.top_productos_mas_utilizados, name='top_productos_salidas'),


    path('api/indicadores/', views.indicadores_dashboard, name='indicadores_dashboard'),
    path('recursos-humanos/json/', recursos_humanos_json, name='recursos_humanos_json'),

    path('productos-granel/', views.lista_productos_granel, name='lista_productos_granel'),

    path('pedido/lista/pedidos_produccion', views.lista_pedidos_produccion, name='lista_pedidos_produccion'),

path('pedidos/hoy/json/', views.pedidos_hoy_json, name='pedidos_hoy_json'),


    #Rechazr pedidos de produccion
path('pedidos/rechazar/<int:pedido_id>/', rechazar_pedido_produccion, name='rechazar_pedido_produccion'),


]
