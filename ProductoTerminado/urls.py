from django.urls import path

from ProductoTerminado import views
from ProductoTerminado.views import indicadores_producto_terminado, SalidaPTerminadoListView, indicadores_de_produccion

urlpatterns = [
    path('agregar-producto/', views.agregar_producto, name='agregar_productoPT'),
    path('registrar-entrada/', views.registrar_entrada, name='registrar_entradaPT'),

    path('registrar-salida/', views.registrar_salida, name='registrar_salidaPT'),
    path('registrar-salida-beta/', views.registrar_salida_beta, name='registrar_salidaPT_beta'),

    path('productos/', views.listar_productos, name='listar_productosPT'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_productoPT'),
    path('productos/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_productoPT'),

    path('cortes/terminados/', views.lista_cortes_producto_terminado, name='lista_cortes_producto_terminado'),
    path('cortes/terminados/nuevo/', views.realizar_corte_producto_terminado, name='realizar_corte_producto_terminado'),
    path('cortes/terminados/<int:pk>/', views.detalle_corte_producto_terminado,
         name='detalle_corte_producto_terminado'),

    path(
        'cortes/terminados/<int:pk>/ajustar/',
        views.ajustar_inventario_corte,
        name='ajustar_inventario_corte'
    ),

    # Ruras para presentacion de producto terminado
    path('listaPresentacionPT/', views.lista_presentaciones, name='lista_presentaciones'),
    path('crearPresentacionPT/', views.crear_presentacion, name='crear_presentacion'),
    path('editarPresentacionPT/<int:pk>/', views.editar_presentacion, name='editar_presentacion'),
    path('eliminarPresentacionPT/<int:pk>/', views.eliminar_presentacion, name='eliminar_presentacion'),

    # Rutas para gramaje de productos terminados

    path('listaGramajePT/', views.lista_gramajes, name='lista_gramajes'),
    path('crearGramajePT/', views.crear_gramaje, name='crear_gramaje'),
    path('editarGramajePT/<int:pk>/', views.editar_gramaje, name='editar_gramaje'),
    path('eliminarGramajePT/<int:pk>/', views.eliminar_gramaje, name='eliminar_gramaje'),

    # DASBOAR

    path('api/indicadoresPT/', indicadores_producto_terminado, name='api_indicadores'),

    # Graficas para el saboard pruebas#

    path('api/ventas_por_dia/', views.ventas_por_dia),
    path('api/productos_mas_vendidos/', views.productos_mas_vendidos),
    path('api/stock_productos/', views.stock_productos),
    path('api/diferencias_inventario/', views.diferencias_inventario),

    path('salidas/', SalidaPTerminadoListView.as_view(), name='lista_salidas_termindo'),

    path('productos-terminados/', views.lista_productos_terminados, name='lista_productos_terminados'),

    # DASBOAR
    path('api/entradas-salidas/PT/', views.entradas_salidas_por_dia_terminado, name='entradas_salidasPT'),
    path('api/top-productos-salidas/PT/', views.top_productos_mas_utilizados_terminado, name='top_productos_salidasPT'),

    path('api/indicadoresProduccion/', indicadores_de_produccion, name='api_indicadoresProduccion'),
]
