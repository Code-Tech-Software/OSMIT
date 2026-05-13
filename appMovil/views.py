from datetime import datetime, timedelta
from django.shortcuts import render
from rest_framework import viewsets
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.timezone import make_aware, is_naive
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ProductoTerminado.models import SalidaPTerminado, DetalleSalidaPTerminado
from appMovil.serializers import *

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import (
    PedidoReabastecimiento,
    MiniBodega,
    MiniBodegaDetalle,
)

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


# Create your views here.

class BaseSyncViewSet(viewsets.ModelViewSet):
   def get_queryset(self):
        queryset = super().get_queryset().all()  # 🔥 ESTO ES LA CLAVE

        return queryset
   

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


class AbonoViewSet(BaseSyncViewSet):
    queryset = Abono.objects.all()
    serializer_class = AbonoSerializer

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



# 1. Ver lista de pedidos pendientes
def lista_pedidos(request):
    # Filtramos solo los pedidos activos (pendientes) y ordenamos por ID descendente
    pedidos = PedidoReabastecimiento.objects.filter(estado=True).order_by('-id')
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

        # Buscar la MiniBodega para esta ruta
        minibodega = MiniBodega.objects.filter(ruta=pedido.ruta).last()

        if not minibodega:
            messages.error(request, f"No se encontró una MiniBodega para la ruta {pedido.ruta.nombre}.")
            return redirect('detalle_pedido_reparto', pedido_id=pedido.id)

        try:
            with transaction.atomic():  # Transacción atómica: Todo o nada

                # 🔥 REACTIVAR PARA EL NUEVO DÍA
                minibodega.estado = True
                minibodega.save()

                # ✅ NUEVO: Actualizar TODO el inventario de la minibodega antes de agregar lo nuevo.
                # Esto iguala la cantidad_inicial a la cantidad_actual para los productos
                # que sobraron ayer, aunque hoy no se hayan pedido.
                MiniBodegaDetalle.objects.filter(mini_bodega=minibodega).update(
                    cantidad_inicial=F('cantidad_actual')
                )

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
                    mb_detalle, created = MiniBodegaDetalle.objects.get_or_create(
                        mini_bodega=minibodega,
                        producto_variacion=variacion,
                        defaults={
                            'cantidad_inicial': cantidad_pedida,
                            'cantidad_actual': cantidad_pedida
                        }
                    )

                    if not created:
                        # ✅ MODIFICADO: Sumar la nueva carga a ambas cantidades
                        # Como ya igualamos inicial = actual antes del bucle,
                        # ahora solo sumamos la cantidad de reabastecimiento a ambas.
                        mb_detalle.cantidad_actual += cantidad_pedida
                        mb_detalle.cantidad_inicial = mb_detalle.cantidad_actual
                        mb_detalle.save()

                # 5. Marcar el pedido como procesado (inactivo)
                pedido.estado = False
                pedido.save()

            messages.success(request,
                             f"Pedido #{pedido.id} reabastecido con éxito. Stock actualizado y minibodega reactivada.")
            return redirect('lista_pedidos_reparto')

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('detalle_pedido_reparto', pedido_id=pedido.id)
        except Exception as e:
            messages.error(request, f"Ocurrió un error al procesar: {str(e)}")
            return redirect('detalle_pedido_reparto', pedido_id=pedido.id)

    return redirect('lista_pedidos_reparto')
from django.shortcuts import render, get_object_or_404
from .models import MiniBodega


# Vista para el listado
def minibodega_list(request):
    # Traemos todas las mini bodegas, ordenadas de la más reciente a la más vieja
    minibodegas = MiniBodega.objects.all().order_by('-fecha', '-id')

    # Mandamos el contexto al template
    context = {
        'minibodegas': minibodegas
    }
    return render(request, 'appMovil/miniBodegas/minibodega_list.html', context)


# Vista para el detalle
def minibodega_detail(request, pk):
    # Buscamos la mini bodega por su ID (Primary Key). Si no existe, lanza un 404.
    minibodega = get_object_or_404(MiniBodega, pk=pk)

    # Mandamos el objeto al template
    context = {
        'minibodega': minibodega
    }
    return render(request, 'appMovil/miniBodegas/minibodega_detail.html', context)

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import MiniBodegaForm

def agregar_minibodega(request):
    if request.method == 'POST':
        form = MiniBodegaForm(request.POST)
        if form.is_valid():
            form.save()
            # Esto activará la notificación Notyf que ya tienes en tu HTML base
            messages.success(request, 'Mini Bodega agregada exitosamente.')
            return redirect('minibodega_lista')
        else:
            messages.error(request, 'Error al guardar. Revisa los datos del formulario.')
    else:
        form = MiniBodegaForm()

    context = {
        'form': form
    }
    return render(request, 'appMovil/miniBodegas/minibodega_form.html', context)