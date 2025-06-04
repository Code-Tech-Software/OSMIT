from django.urls import path

from VehiculosRutas import views


urlpatterns = [
    path('listarVehiculos/', views.listar_vehiculos, name='listar_vehiculos'),
    path('agregarVehiculos/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('editarVehiculos/<int:pk>/', views.editar_vehiculo, name='editar_vehiculo'),
    path('eliminarVehiculos/<int:pk>/', views.eliminar_vehiculo, name='eliminar_vehiculo'),

    # rutas

    path('listarRutas/', views.listar_rutas, name='listar_rutas'),
    path('agregarRutas/', views.agregar_ruta, name='agregar_ruta'),
    path('editarRutas/<int:pk>/', views.editar_ruta, name='editar_ruta'),
    path('eliminarRutas/<int:pk>/', views.eliminar_ruta, name='eliminar_ruta'),


    #VENTAS
    path('venta/', views.lista_ventas_cliente, name='ventas_lista'),  # lista principal
    path('venta/<int:venta_id>/', views.venta_cliente_detalle, name='venta_cliente_detalle'),
    path('por-dia/', views.ventas_por_dia, name='ventas_por_dia'),
    path('por-dia/<str:fecha>/<int:user_id>/', views.detalle_ventas_dia, name='detalle_ventas_dia'),
    # tu ruta existente

    # nueva ruta para procesar
    path('detalle-ventas/<fecha>/<int:user_id>/procesar/',
         views.procesar_ventas_dia,
         name='procesar_ventas_dia'),

    # CLIENTES

    path('listarClientes/', views.listar_clientes, name='listar_clientes'),
    path('agregarClientes/', views.agregar_cliente, name='agregar_cliente'),
    path('editarClientes/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('eliminarClientes/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('editar-dias-visita/<int:cliente_id>/', views.editar_dias_visita, name='editar_dias_visita'),

    path('clientes/pdf/', views.descargar_clientes_pdf, name='descargar_clientes_pdf'),



]
