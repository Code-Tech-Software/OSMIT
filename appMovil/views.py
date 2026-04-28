from datetime import datetime, timedelta
from django.shortcuts import render
from rest_framework import viewsets
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.timezone import make_aware, is_naive
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ProductoTerminado.models import SalidaPTerminado, DetalleSalidaPTerminado
from appMovil.serializers import *

# Create your views here.

class BaseSyncViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        #print("🔥 Sync FULL: enviando TODOS los registros")
        return self.queryset

class RolViewSet(BaseSyncViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer


class UsuarioViewSet(BaseSyncViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer


class CategoriaProductoViewSet(BaseSyncViewSet):
    queryset = CategoriaProducto.objects.all()
    serializer_class = CategoriaProductoSerializer


class PresentacionProductoTerminadoViewSet(BaseSyncViewSet):
    queryset = PresentacionProductoTerminado.objects.all()
    serializer_class = PresentacionProductoTerminadoSerializer


class ProductoTerminadoViewSet(BaseSyncViewSet):
    queryset = ProductoTerminado.objects.all()
    serializer_class = ProductoTerminadoSerializer


class ProductoVariacionViewSet(BaseSyncViewSet):
    queryset = ProductoVariacion.objects.all()
    serializer_class = ProductoVariacionSerializer


class VehiculoViewSet(BaseSyncViewSet):
    queryset = Vehiculo.objects.all()
    serializer_class = VehiculoSerializer


class RutaViewSet(BaseSyncViewSet):
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer


class ClienteViewSet(BaseSyncViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer


class ClienteDiasVisitaViewSet(BaseSyncViewSet):
    queryset = ClienteDiasVisita.objects.all()
    serializer_class = ClienteDiasVisitaSerializer


class MiniBodegaViewSet(BaseSyncViewSet):
    queryset = MiniBodega.objects.all()
    serializer_class = MiniBodegaSerializer


class MiniBodegaDetalleViewSet(BaseSyncViewSet):
    queryset = MiniBodegaDetalle.objects.all()
    serializer_class = MiniBodegaDetalleSerializer


class VentaViewSet(BaseSyncViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer


class VentaDetalleViewSet(BaseSyncViewSet):
    queryset = VentaDetalle.objects.all()
    serializer_class = VentaDetalleSerializer


class PedidoReabastecimientoViewSet(BaseSyncViewSet):
    queryset = PedidoReabastecimiento.objects.all()
    serializer_class = PedidoReabastecimientoSerializer


class PedidoReabastecimientoDetalleViewSet(BaseSyncViewSet):
    queryset = PedidoReabastecimientoDetalle.objects.all()
    serializer_class = PedidoReabastecimientoDetalleSerializer


"""
{
  "mini_bodega_id": 1,
  "productos": [
    {
      "producto_variacion_id": 1,
      "cantidad_actual": 5
    },
    {
      "producto_variacion_id": 2,
      "cantidad_actual": 0
    }
  ]
}
"""


@api_view(['POST'])
def cerrar_mini_bodega(request):
    serializer = CerrarMiniBodegaSerializer2(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data
    mini_bodega_id = data['mini_bodega_id']
    productos = data['productos']

    try:
        mini_bodega = MiniBodega.objects.get(id=mini_bodega_id)
    except MiniBodega.DoesNotExist:
        return Response({"error": "Mini bodega no encontrada"}, status=404)

    # 🚫 Evitar doble cierre
    if not mini_bodega.estado:
        return Response({"error": "La mini bodega ya está cerrada"}, status=400)

    for item in productos:
        try:
            detalle = MiniBodegaDetalle.objects.get(
                mini_bodega=mini_bodega,
                producto_variacion_id=item['producto_variacion_id']
            )

            cantidad = item['cantidad_actual']

            # 🔹 Validaciones básicas
            if cantidad < 0:
                return Response({"error": "Cantidad negativa no permitida"}, status=400)

            if cantidad > detalle.cantidad_inicial:
                return Response({"error": "Cantidad mayor a la inicial"}, status=400)

            detalle.cantidad_actual = cantidad
            detalle.save()

        except MiniBodegaDetalle.DoesNotExist:
            continue

    # 🔹 Cerrar mini bodega
    mini_bodega.estado = False
    mini_bodega.save()

    return Response({"message": "Cierre realizado correctamente"})


"""
{
  "ruta_id": 1,
  "productos": [
    {
      "producto_variacion_id": 1,
      "cantidad": 20
    },
    {
      "producto_variacion_id": 2,
      "cantidad": 10
    }
  ]
}
"""


@api_view(['POST'])
def crear_reabastecimiento(request):
    serializer = CrearPedidoReabastecimientoSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data
    ruta_id = data['ruta_id']
    productos = data['productos']

    if not productos:
        return Response({"error": "Debe enviar productos"}, status=400)

    try:
        ruta = Ruta.objects.get(id=ruta_id)
    except Ruta.DoesNotExist:
        return Response({"error": "Ruta no encontrada"}, status=404)

    # 🔥 AQUÍ SACAS EL USUARIO
    usuario = ruta.usuario

    pedido = PedidoReabastecimiento.objects.create(
        ruta=ruta,
        usuario=usuario
    )

    for item in productos:
        PedidoReabastecimientoDetalle.objects.create(
            pedido=pedido,
            producto_variacion_id=item['producto_variacion_id'],
            cantidad=item['cantidad']
        )

    return Response({
        "message": "Pedido creado correctamente",
        "pedido_id": pedido.id
    })


"""
{
  "pedido_id": 1
}
"""


@api_view(['POST'])
def sincronizar_reabastecimiento(request):
    pedido_id = request.data.get("pedido_id")

    try:
        pedido = PedidoReabastecimiento.objects.get(id=pedido_id)
    except PedidoReabastecimiento.DoesNotExist:
        return Response({"error": "Pedido no encontrado"}, status=404)

    try:
        mini_bodega = MiniBodega.objects.get(
            usuario=pedido.ruta.usuario
        )
    except MiniBodega.DoesNotExist:
        return Response({"error": "Mini bodega no encontrada"}, status=404)

    # 🔥 REACTIVAR PARA EL NUEVO DÍA
    mini_bodega.estado = True
    mini_bodega.save()

    detalles_pedido = PedidoReabastecimientoDetalle.objects.filter(
        pedido=pedido
    )

    for det in detalles_pedido:

        pv = det.producto_variacion
        cantidad = det.cantidad

        detalle_mb, created = MiniBodegaDetalle.objects.get_or_create(
            mini_bodega=mini_bodega,
            producto_variacion=pv,
            defaults={
                "cantidad_inicial": cantidad,
                "cantidad_actual": cantidad
            }
        )

        if not created:
            # SUMAR AL STOCK ACTUAL
            detalle_mb.cantidad_actual += cantidad
            # REINICIAR STOCK INICIAL (NUEVO DÍA)
            detalle_mb.cantidad_inicial = detalle_mb.cantidad_actual
            detalle_mb.save()

    return Response({
        "message": "Stock actualizado y minibodega reactivada"
    })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import (
    PedidoReabastecimiento,
    MiniBodega,
    MiniBodegaDetalle,
)


# 1. Ver lista de pedidos pendientes
def lista_pedidos(request):
    # Filtramos solo los pedidos activos (pendientes)
    pedidos = PedidoReabastecimiento.objects.filter(estado=True).order_by('-fecha')
    return render(request, 'appMovil/reabastecimiento/lista_pedidos.html', {'pedidos': pedidos})


# 2. Ver detalles del pedido
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(PedidoReabastecimiento, id=pedido_id)
    detalles = pedido.pedidoreabastecimientodetalle_set.all()
    return render(request, 'appMovil/reabastecimiento/detalle_pedido.html', {'pedido': pedido, 'detalles': detalles})


# 3. Procesar el Reabastecimiento
def procesar_reabastecimiento(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(PedidoReabastecimiento, id=pedido_id, estado=True)
        detalles = pedido.pedidoreabastecimientodetalle_set.all()

        # Buscar la MiniBodega activa para esta ruta
        minibodega = MiniBodega.objects.filter(ruta=pedido.ruta, estado=True).last()

        if not minibodega:
            messages.error(request, f"No se encontró una MiniBodega activa para la ruta {pedido.ruta.nombre}.")
            return redirect('detalle_pedido', pedido_id=pedido.id)

        try:
            with transaction.atomic():  # Transacción atómica: Todo o nada
                # 1. Crear el registro de Salida
                salida = SalidaPTerminado.objects.create(
                    fecha_salida=timezone.now(),
                    usuario=request.user,
                    ruta=pedido.ruta,
                    destino='opcion1',  # Asumiendo que opcion1 es 'Ruta'
                    nota=f"Salida generada por reabastecimiento. Pedido #{pedido.id}"
                )

                for item in detalles:
                    variacion = item.producto_variacion
                    cantidad_pedida = item.cantidad

                    # 1.1 Verificar si hay stock suficiente en la bodega principal
                    if variacion.stock < cantidad_pedida:
                        raise ValueError(
                            f"Stock insuficiente para {variacion}. Stock actual: {variacion.stock}, Pedido: {cantidad_pedida}")

                    # 2. Descontar del stock principal
                    variacion.stock -= cantidad_pedida
                    variacion.save()

                    # 3. Crear Detalle de Salida
                    DetalleSalidaPTerminado.objects.create(
                        salida_p_terminado=salida,
                        producto_variacion=variacion,
                        cantidad=cantidad_pedida
                    )

                    # 4. Ingresar a la MiniBodega del repartidor
                    # Obtenemos el detalle si el producto ya está en la minibodega, si no, lo creamos
                    mb_detalle, created = MiniBodegaDetalle.objects.get_or_create(
                        mini_bodega=minibodega,
                        producto_variacion=variacion,
                        defaults={
                            'cantidad_inicial': 0,  # O la cantidad pedida si es la primera vez
                            'cantidad_actual': 0
                        }
                    )

                    # Sumamos la cantidad al stock actual de su camioneta/minibodega
                    mb_detalle.cantidad_actual += cantidad_pedida
                    mb_detalle.save()

                # 5. Marcar el pedido como procesado (inactivo)
                pedido.estado = False
                pedido.save()

            messages.success(request, f"Pedido #{pedido.id} reabastecido con éxito. Stock actualizado.")
            return redirect('lista_pedidos')

        except ValueError as e:
            # Capturamos el error de falta de stock
            messages.error(request, str(e))
            return redirect('detalle_pedido', pedido_id=pedido.id)
        except Exception as e:
            # Capturamos cualquier otro error inesperado
            messages.error(request, f"Ocurrió un error al procesar: {str(e)}")
            return redirect('detalle_pedido', pedido_id=pedido.id)

    return redirect('lista_pedidos')