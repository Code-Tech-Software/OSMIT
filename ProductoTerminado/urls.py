from django.urls import path

from ProductoTerminado import views
from ProductoTerminado.views import indicadores_de_produccion

urlpatterns = [
    path('agregar-producto/', views.agregar_producto, name='agregar_productoPT'),
    path('registrar-entrada/', views.registrar_entrada, name='registrar_entradaPT'),

    path('registrar-salida/', views.registrar_salida, name='registrar_salidaPT'),

    path('productos/', views.listar_productos, name='listar_productosPT'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_productoPT'),
    path('productos/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_productoPT'),

    # Ruras para presentacion de producto terminado
    path('listaPresentacionPT/', views.lista_presentaciones, name='lista_presentaciones'),
    path('crearPresentacionPT/', views.crear_presentacion, name='crear_presentacion'),
    path('editarPresentacionPT/<int:pk>/', views.editar_presentacion, name='editar_presentacion'),
    path('eliminarPresentacionPT/<int:pk>/', views.eliminar_presentacion, name='eliminar_presentacion'),

    # DASBOAR

    path('api/stock_productos/', views.stock_productos),

    path('productos-terminados/', views.lista_productos_terminados, name='lista_productos_terminados'),

    # DASBOAR
    path('api/entradas-salidas/PT/', views.entradas_salidas_por_dia_terminado, name='entradas_salidasPT'),
    path('api/top-productos-salidas/PT/', views.top_productos_mas_utilizados_terminado, name='top_productos_salidasPT'),

    path('api/indicadoresProduccion/', indicadores_de_produccion, name='api_indicadoresProduccion'),

    path('api/indicadoresPT/', views.api_indicadores_pt, name='api_indicadores_pt'),

]
