from datetime import datetime, timedelta
from django.shortcuts import render
from rest_framework import viewsets, status
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.timezone import make_aware, is_naive
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from decimal import Decimal
from django.contrib.auth.decorators import login_required
import secrets
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from ProductoTerminado.models import SalidaPTerminado, DetalleSalidaPTerminado, EntradaPTerminado, \
    DetalleEntradaPTerminado
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
from .models import Dispositivo

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .forms import DispositivoForm
from .autenticacion_dispositivo import DispositivoActivoPermission


# Create your views here.

class BaseSyncViewSet(viewsets.ModelViewSet):
    permission_classes = [DispositivoActivoPermission]

    def get_queryset(self):
        queryset = super().get_queryset().all()

        return queryset
   

class RolViewSet(BaseSyncViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer


class UsuarioViewSet(BaseSyncViewSet):
    queryset = Usuario.objects.filter(
        rol__nombre="Repartidor",
        rol__estado=True
    )
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

## Esto no se usa como tal nomas esta por que si
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
@permission_classes([DispositivoActivoPermission])
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




{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
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
@api_view(['POST'])
@permission_classes([DispositivoActivoPermission])
def crear_reabastecimiento(request):
    data = request.data

    ruta_id = data.get('ruta_id')
    productos = data.get('productos')
    pedido_uuid = data.get('uuid')  # 🔥 UUID del pedido

    if not ruta_id:
        return Response({"error": "ruta_id es requerido"}, status=400)

    if not productos:
        return Response({"error": "Debe enviar productos"}, status=400)

    if not pedido_uuid:
        return Response({"error": "uuid es requerido"}, status=400)

    try:
        ruta = Ruta.objects.get(id=ruta_id)
    except Ruta.DoesNotExist:
        return Response({"error": "Ruta no encontrada"}, status=404)

    usuario = ruta.usuario

    if not usuario:
        return Response({"error": "La ruta no tiene usuario asignado"}, status=400)

    # 🔥 Evitar duplicados
    if PedidoReabastecimiento.objects.filter(uuid=pedido_uuid).exists():
        return Response({
            "message": "Este pedido ya fue registrado",
            "pedido_uuid": pedido_uuid
        }, status=200)

    # 🔥 Crear pedido
    pedido = PedidoReabastecimiento.objects.create(
        uuid=pedido_uuid,
        ruta=ruta,
        usuario=usuario
    )

    # 🔥 Crear detalles
    for item in productos:
        PedidoReabastecimientoDetalle.objects.create(
            pedido=pedido,
            pedido_uuid=pedido_uuid,
            producto_variacion_id=item['producto_variacion_id'],
            cantidad=item['cantidad']
        )

    return Response({
        "message": "Pedido creado correctamente",
        "pedido_uuid": pedido.uuid
    }, status=201)




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
@login_required
def lista_pedidos(request):
    # Filtramos solo los pedidos activos (pendientes) y ordenamos por ID descendente
    pedidos = PedidoReabastecimiento.objects.filter(estado=True).order_by('-id')
    return render(request, 'appMovil/reabastecimiento/lista_pedidos.html', {'pedidos': pedidos})


# 2. Ver detalles del pedido
@login_required
def detalle_pedido(request, pedido_id):
    pedido = get_object_or_404(PedidoReabastecimiento, id=pedido_id)
    detalles = pedido.pedidoreabastecimientodetalle_set.all()
    return render(request, 'appMovil/reabastecimiento/detalle_pedido.html', {'pedido': pedido, 'detalles': detalles})


# 3. Procesar el Reabastecimiento

@login_required
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
                    cantidad=cantidad_pedida,
                    precio_unitario=variacion.precio
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

                MiniBodegaDetalle.objects.filter(
                mini_bodega=minibodega,
                cantidad_actual=0
                ).delete()

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
@login_required
def minibodega_list(request):
    # Traemos todas las mini bodegas, ordenadas de la más reciente a la más vieja
    minibodegas = MiniBodega.objects.all().order_by('-fecha', '-id')

    # Mandamos el contexto al template
    context = {
        'minibodegas': minibodegas
    }
    return render(request, 'appMovil/miniBodegas/minibodega_list.html', context)


# Vista para el detalle
@login_required
def minibodega_detail(request, pk):
    # Buscamos la mini bodega por su ID (Primary Key). Si no existe, lanza un 404.
    minibodega = get_object_or_404(MiniBodega, pk=pk)
    context = {
        'minibodega': minibodega
    }
    return render(request, 'appMovil/miniBodegas/minibodega_detail.html', context)





from django.http import JsonResponse
from django.contrib.auth.decorators import login_required



@login_required
def abrir_minibodega_manual(request, pk):

    if request.method == 'POST':

        try:
            minibodega = get_object_or_404(
                MiniBodega,
                pk=pk
            )

            # Eliminar productos que ya no tienen existencia
            MiniBodegaDetalle.objects.filter(
                mini_bodega=minibodega,
                cantidad_actual=0
            ).delete()

            # Lo que quedó pasa a ser el nuevo inicial
            MiniBodegaDetalle.objects.filter(
                mini_bodega=minibodega,
                cantidad_actual__gt=0
            ).update(
                cantidad_inicial=F('cantidad_actual')
            )

            # Abrir MiniBodega
            minibodega.estado = True
            minibodega.save()

            return JsonResponse({
                'success': True,
                'message': 'La Mini Bodega ha sido abierta exitosamente.'
            })

        except Exception as e:

            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    }, status=405)

import json
@login_required
def regresar_producto_bodega(request, detalle_pk):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cantidad_a_regresar = Decimal(str(data.get('cantidad', 0)))

            if cantidad_a_regresar <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'La cantidad debe ser mayor a 0.'
                })

            with transaction.atomic():

                detalle = (
                    MiniBodegaDetalle.objects
                    .select_for_update()
                    .get(pk=detalle_pk)
                )

                if cantidad_a_regresar > detalle.cantidad_actual:
                    return JsonResponse({
                        'success': False,
                        'message': 'No puedes regresar más de lo que hay en la Mini Bodega.'
                    })

                # Guardamos la MiniBodega y producto antes de modificar/eliminar
                minibodega = detalle.mini_bodega

                variacion = (
                    ProductoVariacion.objects
                    .select_for_update()
                    .get(pk=detalle.producto_variacion.id)
                )

                # 1. Restar de la MiniBodega
                detalle.cantidad_actual -= cantidad_a_regresar

                # 2. La cantidad que queda se convierte en la nueva inicial
                detalle.cantidad_inicial = detalle.cantidad_actual

                # 3. Si ya no queda producto, eliminar el detalle
                if detalle.cantidad_actual == 0:
                    detalle.delete()
                else:
                    detalle.save()

                # 4. Sumar al stock principal
                variacion.stock += cantidad_a_regresar
                variacion.save()

                # 5. Registrar la entrada para historial
                entrada = EntradaPTerminado.objects.create(
                    fecha_entrada=timezone.now(),
                    usuario=request.user,
                    nota=(
                        f"Retorno desde Mini Bodega #{minibodega.id} "
                        f"(Ruta: {minibodega.ruta.nombre})"
                    )
                )

                DetalleEntradaPTerminado.objects.create(
                    entrada_p_terminado=entrada,
                    producto_variacion=variacion,
                    cantidad=cantidad_a_regresar
                )

            return JsonResponse({
                'success': True,
                'message': 'El stock ha sido regresado a la bodega principal.'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    }, status=405)





# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import MiniBodegaForm, FiltroDevolucionesForm


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


##Nuevas apis 

"""
{
  "ventas": [
    {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "usuario_id": 2,
      "cliente_id": 10,
      "total": 150.00,
      "tipo_venta": "CREDITO",
      "fecha": "2026-05-19T10:02:10"
    },
    {
      "uuid": "22222222-2222-2222-2222-222222222222",
      "usuario_id": 2,
      "cliente_id": null,
      "total": 80.00,
      "tipo_venta": "CONTADO",
      "fecha": "2026-05-19T11:15:00"
    }
  ],
  "detalles": [
    {
      "uuid": "aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
      "venta_uuid": "11111111-1111-1111-1111-111111111111",
      "producto_variacion_id": 5,
      "cantidad": 2,
      "precio_unitario": 50.00,
      "nombre_producto": "Coca 600ml"
    }
  ]
}
"""

@api_view(['POST'])
@permission_classes([DispositivoActivoPermission])
def sync_ventas(request):
    data = request.data

    ventas = data.get('ventas', [])
    detalles = data.get('detalles', [])

    ventas_cache = {}

    with transaction.atomic():

        # =========================
        # 🔥 VENTAS
        # =========================
        for v in ventas:

            if Venta.objects.filter(uuid=v.get('uuid')).exists():
                continue

            usuario = Usuario.objects.filter(id=v.get('usuario_id')).first()
            if not usuario:
                continue

            cliente = None
            if v.get('cliente_id'):
                cliente = Cliente.objects.filter(id=v.get('cliente_id')).first()

            total = Decimal(str(v.get('total', 0)))
            tipo = v.get('tipo_venta', 'CONTADO')

            if total <= 0:
                continue

            # 🔥 lógica de pago
            if tipo == "CONTADO":
                estado = "PAGADO"
                saldo = 0
            else:
                estado = "PENDIENTE"
                saldo = total

            # 🔥 FECHA (OBLIGATORIA)
            fecha_str = v.get('fecha')

            if fecha_str:
                try:
                    fecha = datetime.fromisoformat(fecha_str)

                 # 🔥 convertir a timezone si viene sin zona
                    if timezone.is_naive(fecha):
                        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())

                except:
                    fecha = timezone.now()
            else:
                fecha = timezone.now()

            venta = Venta.objects.create(
                uuid=v.get('uuid'),
                cliente=cliente,
                usuario=usuario,
                total=total,
                tipo_venta=tipo,
                estado_pago=estado,
                saldo_pendiente=saldo,
                fecha=fecha
            )

            # 🔥 actualizar cliente si es crédito
            if tipo == "CREDITO" and cliente:
                cliente.saldo_adeudo += Decimal(str(total))
                cliente.save()

            ventas_cache[str(v.get('uuid'))] = venta

        # =========================
        # 🔥 DETALLES
        # =========================
        for d in detalles:

            if VentaDetalle.objects.filter(uuid=d.get('uuid')).exists():
                continue

            venta = ventas_cache.get(d.get('venta_uuid')) \
                or Venta.objects.filter(uuid=d.get('venta_uuid')).first()

            if not venta:
                raise Exception(f"Venta no encontrada para detalle {d.get('uuid')}")

            VentaDetalle.objects.create(
                uuid=d.get('uuid'),
                venta=venta,
                producto_variacion_id=d.get('producto_variacion_id'),
                cantidad=d.get('cantidad'),
                precio_unitario=d.get('precio_unitario'),
                nombre_producto=d.get('nombre_producto', 'Producto')
            )

    return Response({
        "message": "Ventas sincronizadas correctamente"
    })


"""
{
  "abonos": [
    {
      "uuid": "33333333-3333-3333-3333-333333333333",
      "venta_uuid": "11111111-1111-1111-1111-111111111111",
      "usuario_id": 5,
      "monto": 50.00,
      "fecha": "2026-05-19T10:02:10"
    },
    {
      "uuid": "44444444-4444-4444-4444-444444444444",
      "venta_uuid": "11111111-1111-1111-1111-111111111111",
      "usuario_id": 5,
      "monto": 100.00,
      "fecha": "2026-05-19T11:15:00"
    }
  ]
}
"""
@api_view(['POST'])
@permission_classes([DispositivoActivoPermission])
def sync_abonos(request):
    data = request.data
    abonos = data.get('abonos', [])

    with transaction.atomic():

        for a in abonos:

            # 🔒 evitar duplicados
            if Abono.objects.filter(uuid=a.get('uuid')).exists():
                continue

            # 🔒 venta segura
            venta = Venta.objects.filter(uuid=a.get('venta_uuid')).first()
            if not venta:
                continue
                #raise Exception(f"Venta no encontrada para abono {a.get('uuid')}")

            # 🔒 usuario seguro
            usuario = Usuario.objects.filter(id=a.get('usuario_id')).first()
            if not usuario:
                continue

            monto = Decimal(str(a.get('monto', 0)))

            if monto <= 0:
                raise Exception(f"Monto inválido en abono {a.get('uuid')}")

            # 🔥 fecha desde Android
            fecha_str = a.get('fecha')

            if fecha_str:
                try:
                    fecha = datetime.fromisoformat(fecha_str)

                 # 🔥 convertir a timezone si viene sin zona
                    if timezone.is_naive(fecha):
                        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())

                except:
                    fecha = timezone.now()
            else:
                fecha = timezone.now()

            # 🔥 crear abono
            Abono.objects.create(
                uuid=a.get('uuid'),
                venta=venta,
                venta_uuid=a.get('venta_uuid'),
                usuario=usuario,
                monto=monto,
                fecha=fecha
            )

            # =========================
            # 🔥 ACTUALIZAR VENTA
            # =========================
            venta.saldo_pendiente -= monto

            if venta.saldo_pendiente <= 0:
                venta.saldo_pendiente = 0
                venta.estado_pago = "PAGADO"

            elif venta.saldo_pendiente < venta.total:
                venta.estado_pago = "PARCIAL"

            else:
                venta.estado_pago = "PENDIENTE"

            venta.save()

            # =========================
            # 🔥 ACTUALIZAR CLIENTE
            # =========================
            if venta.cliente:
                cliente = venta.cliente

                cliente.saldo_adeudo -= monto

                if cliente.saldo_adeudo < 0:
                    cliente.saldo_adeudo = 0

                cliente.save()

    return Response({
        "message": "Abonos sincronizados correctamente"
    })





"""
{
  "devoluciones": [
    {
      "uuid": "11111111-1111-1111-1111-111111111111",
      "tipo": "DEVOLUCION_VENTA",
      "cliente_id": 10,

      "usuario_id": 3,
      "mini_bodega_id": 1,

      "fecha": "2026-05-21T14:30:00",
      "descripcion": "Producto en mal estado"
    }
  ],
  "detalles": [
    {
      "uuid": "22222222-2222-2222-2222-222222222222",
      "devolucion_uuid": "11111111-1111-1111-1111-111111111111",
      "producto_variacion_id": 5,
      "cantidad": 2,
      "precio_unitario": 15.50
    }
  ],
  "mermas": [
    {
      "uuid": "33333333-3333-3333-3333-333333333333",
      "mini_bodega_id": 1,
      "producto_variacion_id": 5,
      "cantidad": 2,
      "devolucion_uuid": "11111111-1111-1111-1111-111111111111"
    }
  ]
}
"""
@api_view(['POST'])
@permission_classes([DispositivoActivoPermission])
def sync_devoluciones(request):
    data = request.data

    devoluciones = data.get('devoluciones', [])
    detalles = data.get('detalles', [])
    mermas = data.get('mermas', [])

    with transaction.atomic():

        # 🔹 1. DEVOLUCIONES
        for d in devoluciones:

            if Devolucion.objects.filter(uuid=d['uuid']).exists():
                continue  # evitar duplicados

            if not Usuario.objects.filter(id=d['usuario_id']).exists():
                continue

            if not MiniBodega.objects.filter(id=d['mini_bodega_id']).exists():
                continue

            fecha_str = d.get('fecha')

            if fecha_str:
                try:
                    fecha = datetime.fromisoformat(fecha_str)

                 # 🔥 convertir a timezone si viene sin zona
                    if timezone.is_naive(fecha):
                        fecha = timezone.make_aware(fecha, timezone.get_current_timezone())

                except:
                    fecha = timezone.now()
            else:
                fecha = timezone.now()

            Devolucion.objects.create(
                uuid=d['uuid'],
                tipo=d['tipo'],
                cliente_id=d.get('cliente_id'),

                # 🔥 ahora vienen directo de la app
                usuario_id=d['usuario_id'],
                mini_bodega_id=d['mini_bodega_id'],

                fecha=fecha,
                descripcion=d.get('descripcion', ''),
                sincronizado=True
    )

        # 🔹 2. DETALLES
        for det in detalles:

            if DevolucionDetalle.objects.filter(uuid=det['uuid']).exists():
                continue

            devolucion = Devolucion.objects.get(uuid=det['devolucion_uuid'])

            DevolucionDetalle.objects.create(
                uuid=det['uuid'],
                devolucion=devolucion,
                devolucion_uuid=det['devolucion_uuid'],
                producto_variacion_id=det['producto_variacion_id'],
                cantidad=det['cantidad'],
                precio_unitario=det.get('precio_unitario', 0)
            )

        # 🔹 3. MERMAS
        for m in mermas:

            if MiniBodegaDetalleMerma.objects.filter(uuid=m['uuid']).exists():
                continue

            devolucion = None
            if m.get('devolucion_uuid'):
                devolucion = Devolucion.objects.get(uuid=m['devolucion_uuid'])

            MiniBodegaDetalleMerma.objects.create(
                uuid=m['uuid'],
                mini_bodega_id=m['mini_bodega_id'],
                producto_variacion_id=m['producto_variacion_id'],
                cantidad=m['cantidad'],
                devolucion=devolucion,
                devolucion_uuid=m.get('devolucion_uuid')
            )

    return Response({
        "message": "Sincronización completada correctamente"
    })


##Solo para revisar
@api_view(['GET'])
def get_ventas(request):

    ventas = Venta.objects.all().order_by('-fecha')

    data = []

    for v in ventas:
        detalles = VentaDetalle.objects.filter(venta=v)

        data.append({
            "uuid": str(v.uuid),
            "cliente": v.cliente.nombre if v.cliente else None,
            "usuario_id": v.usuario.id if v.usuario else None,
            "fecha": v.fecha,
            "total": float(v.total),
            "tipo_venta": v.tipo_venta,
            "estado_pago": v.estado_pago,
            "saldo_pendiente": float(v.saldo_pendiente),

            "detalles": [
                {
                    "producto": d.nombre_producto,
                    "cantidad": float(d.cantidad),
                    "precio_unitario": float(d.precio_unitario)
                }
                for d in detalles
            ]
        })

    return Response(data)

@api_view(['GET'])
def get_abonos(request):

    abonos = Abono.objects.all().order_by('-fecha')

    data = []

    for a in abonos:
        data.append({
            "uuid": str(a.uuid),
            "venta_uuid": str(a.venta.uuid),
            "usuario_id": a.usuario.id,
            "monto": float(a.monto),
            "fecha": a.fecha
        })

    return Response(data)

@api_view(['GET'])
def get_devoluciones(request):

    devoluciones = Devolucion.objects.all().order_by('-fecha')

    data = []

    for d in devoluciones:

        detalles = DevolucionDetalle.objects.filter(devolucion=d)
        mermas = MiniBodegaDetalleMerma.objects.filter(devolucion=d)

        data.append({
            "uuid": str(d.uuid),
            "tipo": d.tipo,
            "cliente": d.cliente.nombre if d.cliente else None,
            "usuario_id": d.usuario.id,
            "mini_bodega_id": d.mini_bodega.id,
            "fecha": d.fecha,
            "descripcion": d.descripcion,

            "detalles": [
                {
                    "producto_variacion_id": det.producto_variacion.id,
                    "cantidad": float(det.cantidad),
                    "precio_unitario": float(det.precio_unitario)
                }
                for det in detalles
            ],

            "mermas": [
                {
                    "producto_variacion_id": m.producto_variacion.id,
                    "cantidad": float(m.cantidad)
                }
                for m in mermas
            ]
        })

    return Response(data)


from django.views.generic import ListView
from django.db.models import Sum
from .models import Venta
from .forms import FiltroVentasForm

class ListaVentasView(ListView):
    model = Venta
    template_name = 'appMovil/ventas/lista_ventas.html'
    context_object_name = 'ventas'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'cliente',
            'usuario'
        )

        hoy = timezone.localdate().strftime('%Y-%m-%d')

        fecha_inicio = self.request.GET.get('fecha_inicio') or hoy
        fecha_fin = self.request.GET.get('fecha_fin') or hoy
        repartidor = self.request.GET.get('repartidor')

        queryset = queryset.filter(
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        )

        if repartidor:
            queryset = queryset.filter(usuario_id=repartidor)

        return queryset.order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoy = timezone.localdate().strftime('%Y-%m-%d')

        fecha_inicio = self.request.GET.get('fecha_inicio') or hoy
        fecha_fin = self.request.GET.get('fecha_fin') or hoy
        repartidor = self.request.GET.get('repartidor')

        context['form'] = FiltroVentasForm({
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'repartidor': repartidor
        })

        # =========================
        # VENTAS
        # =========================

        ventas_filtradas = self.get_queryset()

        # Valor total de todas las ventas realizadas
        total_ventas = ventas_filtradas.aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        # Dinero recibido inmediatamente por ventas de contado
        total_contado = ventas_filtradas.filter(
            tipo_venta='CONTADO'
        ).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        # Valor de ventas hechas a crédito
        total_credito = ventas_filtradas.filter(
            tipo_venta='CREDITO'
        ).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        # =========================
        # ABONOS
        # =========================

        abonos_filtrados = Abono.objects.select_related(
            'venta',
            'venta__cliente',
            'usuario'
        ).filter(
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        )

        if repartidor:
            abonos_filtrados = abonos_filtrados.filter(
                usuario_id=repartidor
            )

        abonos_filtrados = abonos_filtrados.order_by('-fecha')

        total_abonos = abonos_filtrados.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')

        # =========================
        # DINERO REALMENTE RECIBIDO
        # =========================

        total_recibido = total_contado + total_abonos

        context['total_ventas'] = total_ventas
        context['total_contado'] = total_contado
        context['total_credito'] = total_credito

        context['abonos'] = abonos_filtrados
        context['total_abonos'] = total_abonos

        context['total_recibido'] = total_recibido

        return context


from django.views.generic import DetailView
from .models import Venta

class DetalleVentaView(DetailView):
    model = Venta
    template_name = 'appMovil/ventas/detalle_venta.html'
    context_object_name = 'venta'

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'ventadetalle_set__producto_variacion',
            'abonos__usuario'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        venta = self.object

        # Descuento que el cliente tiene actualmente
        porcentaje_descuento_cliente = (
            venta.cliente.porcentaje_descuento
            if venta.cliente
            else Decimal('0.00')
        )

        # Subtotal real de la venta antes del descuento
        subtotal_venta = sum(
            (
                detalle.subtotal
                for detalle in venta.ventadetalle_set.all()
            ),
            Decimal('0.00')
        )

        # El descuento histórico se obtiene de la diferencia
        # entre el subtotal de los productos y el total guardado.
        monto_descuento = subtotal_venta - venta.total

        if monto_descuento < 0:
            monto_descuento = Decimal('0.00')

        # Porcentaje que realmente se aplicó en esa venta
        porcentaje_descuento_venta = Decimal('0.00')

        if subtotal_venta > 0 and monto_descuento > 0:
            porcentaje_descuento_venta = (
                monto_descuento / subtotal_venta
            ) * Decimal('100')

        # Determinar si el porcentaje histórico coincide
        # con el porcentaje actual del cliente.
        descuento_coincide = (
            abs(
                porcentaje_descuento_venta -
                porcentaje_descuento_cliente
            ) < Decimal('0.01')
        )

        context['subtotal_venta'] = subtotal_venta
        context['monto_descuento'] = monto_descuento
        context['porcentaje_descuento_venta'] = porcentaje_descuento_venta
        context['porcentaje_descuento_cliente'] = porcentaje_descuento_cliente
        context['descuento_coincide'] = descuento_coincide

        return context


from django.views.generic import ListView, DetailView
from django.db.models import Sum, F, FloatField
from .models import Devolucion


class ListaDevolucionesView(ListView):
    model = Devolucion
    template_name = 'appMovil/devoluciones/lista_devoluciones.html'
    context_object_name = 'devoluciones'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'cliente',
            'usuario',
            'mini_bodega'
        ).annotate(
            total=Sum(
                F('devoluciondetalle__cantidad') *
                F('devoluciondetalle__precio_unitario'),
                output_field=FloatField()
            )
        )

        hoy = timezone.localdate().strftime('%Y-%m-%d')

        # Obtener parámetros del GET
        fecha_inicio = self.request.GET.get('fecha_inicio') or hoy
        fecha_fin = self.request.GET.get('fecha_fin') or hoy
        repartidor = self.request.GET.get('repartidor')

        # Aplicar filtros de fecha
        queryset = queryset.filter(
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        )

        # Filtrar por repartidor si se seleccionó
        if repartidor:
            queryset = queryset.filter(
                usuario_id=repartidor
            )

        return queryset.order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoy = timezone.localdate().strftime('%Y-%m-%d')

        # Valores actuales de los filtros
        fecha_inicio = self.request.GET.get('fecha_inicio') or hoy
        fecha_fin = self.request.GET.get('fecha_fin') or hoy
        repartidor = self.request.GET.get('repartidor')

        context['form'] = FiltroDevolucionesForm({
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'repartidor': repartidor
        })

        # Total de todas las devoluciones del filtro,
        # no solamente las de la página actual
        devoluciones_filtradas = self.get_queryset()

        total_suma = devoluciones_filtradas.aggregate(
            total_global=Sum(
                F('devoluciondetalle__cantidad') *
                F('devoluciondetalle__precio_unitario'),
                output_field=FloatField()
            )
        )['total_global'] or 0.00

        context['total_suma'] = total_suma

        return context


class DetalleDevolucionView(DetailView):
    model = Devolucion
    template_name = 'appMovil/devoluciones/detalle_devolucion.html'
    context_object_name = 'devolucion'

    def get_queryset(self):
        # Traemos las relaciones y calculamos el total general de esta devolución en específico
        return super().get_queryset().select_related('cliente', 'usuario', 'mini_bodega').prefetch_related(
            'devoluciondetalle_set__producto_variacion'
        ).annotate(
            total=Sum(
                F('devoluciondetalle__cantidad') * F('devoluciondetalle__precio_unitario'),
                output_field=FloatField()
            )
        )

#CARGAR COSAS#

import csv
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Cliente, Ruta
from .forms import CargarCSVForm

@login_required
def cargar_clientes_csv(request):
    if request.method == 'POST':
        form = CargarCSVForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_csv']

            if not archivo.name.endswith('.csv'):
                messages.error(request, 'Por favor, sube un archivo con extensión .csv')
                return redirect('cargar_clientes_csv')

            try:
                # --- SOLUCIÓN PARA EXCEL ---
                try:
                    # Intenta decodificar eliminando el BOM de Excel (el caracter invisible)
                    data_set = archivo.read().decode('utf-8-sig')
                except UnicodeDecodeError:
                    # Si falla por acentos o eñes guardados en formato antiguo, usa latin-1
                    archivo.seek(0)
                    data_set = archivo.read().decode('latin-1')

                io_string = io.StringIO(data_set)
                reader = csv.DictReader(io_string)
                # -----------------------------

                # Usamos transaction.atomic para procesar de forma segura relaciones complejas
                with transaction.atomic():
                    contador_clientes = 0

                    for row in reader:
                        # 1. Buscar la Ruta por ID si viene en el CSV
                        ruta_id = row.get('ruta_id')
                        ruta_obj = None
                        if ruta_id:
                            try:
                                ruta_obj = Ruta.objects.get(id=int(ruta_id))
                            except (Ruta.DoesNotExist, ValueError):
                                pass  # Si no existe, queda como None

                        # 2. Conversión del estado booleano
                        estado_str = str(row.get('estado', 'true')).lower()
                        estado_bool = estado_str in ['true', '1', 'si', 'yes', 'active']

                        # 3. Crear e insertar el Cliente con TODOS sus campos
                        # Aplicamos .strip() al nombre para limpiar espacios residuales
                        cliente = Cliente.objects.create(
                            nombre=row.get('nombre', '').strip(),
                            nombre_negocio=row.get('nombre_negocio', '').strip(),
                            giro=row.get('giro', None),
                            tipo_exhibidor=row.get('tipo_exhibidor', None),
                            direccion=row.get('direccion', '').strip(),
                            localidad=row.get('localidad', None),
                            colonia=row.get('colonia', None),
                            telefono=row.get('telefono', None),
                            limite_credito=float(row.get('limite_credito', 0.00) or 0.00),
                            saldo_adeudo=float(row.get('saldo_adeudo', 0.00) or 0.00),
                            porcentaje_descuento=float(row.get('porcentaje_descuento', 0.00) or 0.00),
                            imagen=row.get('imagen', None),
                            observaciones=row.get('observaciones', None),
                            ruta=ruta_obj,
                            estado=estado_bool
                        )
                        contador_clientes += 1

                        # 4. Procesar los Días de Visita (ClienteDiasVisita)
                        dias_visita_str = row.get('dias_visita', '')
                        if dias_visita_str:
                            lista_dias = [dia.strip().lower() for dia in dias_visita_str.split(',')]
                            dias_validos = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']

                            for dia in lista_dias:
                                if dia in dias_validos:
                                    ClienteDiasVisita.objects.create(
                                        cliente=cliente,
                                        dia_semana=dia
                                    )

                messages.success(request,
                                 f'¡Éxito! Se registraron {contador_clientes} clientes con sus configuraciones y días de visita.')
                return redirect('cargar_clientes_csv')

            except Exception as e:
                messages.error(request, f'Error crítico al procesar el archivo: {e}')
                return redirect('cargar_clientes_csv')

    else:
        form = CargarCSVForm()

    return render(request, 'appMovil/cargaDatos/cargar_csv.html', {'form': form})



import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import  ProductoVariacion

@login_required
def cargar_productos_csv(request):
    if request.method == 'POST':
        form = CargarCSVForm(request.POST, request.FILES)

        if form.is_valid():
            archivo = request.FILES['archivo_csv']

            if not archivo.name.endswith('.csv'):
                messages.error(request, 'El archivo debe tener extensión .csv.')
                return redirect('cargar_productos')  # Asegúrate de que este nombre de URL sea el correcto

            try:
                decoded_file = archivo.read().decode('utf-8-sig').splitlines()
                reader = csv.DictReader(decoded_file)

                with transaction.atomic():
                    for row in reader:
                        # 1. Categoría
                        categoria, _ = CategoriaProducto.objects.get_or_create(
                            nombre=row['categoria'].strip()
                        )

                        producto, _ = ProductoTerminado.objects.get_or_create(
                            nombre=row['producto_nombre'].strip(),
                            defaults={'categoria_producto': categoria}
                        )

                        presentacion, _ = PresentacionProductoTerminado.objects.get_or_create(
                            nombre=row['presentacion'].strip()
                        )

                        codigo_barras = row.get('codigo_barras', '').strip()
                        if not codigo_barras:
                            codigo_barras = None

                        ProductoVariacion.objects.update_or_create(
                            producto=producto,
                            presentacion=presentacion,
                            defaults={
                                'costo': row['costo'],
                                'precio': row['precio'],
                                'stock': row['stock'],
                                'stock_min': row['stock_min'],
                                'codigo_barras': codigo_barras
                            }
                        )

                messages.success(request, 'Todos los productos se cargaron exitosamente.')
                return redirect('cargar_productos')

            except Exception as e:
                # Si algo falla (ej. una letra en un campo decimal), se cancela toda la transacción
                messages.error(request, f'Error procesando el archivo: {str(e)}')
                return redirect('cargar_productos')
        else:
            messages.error(request, 'Por favor, selecciona un archivo válido.')
            return redirect('cargar_productos')

    else:
        form = CargarCSVForm()
    return render(request, 'appMovil/cargaDatos/cargarProductosTerminados_csv.html', {'form': form})



@login_required
def registrar_dispositivo(request):

    if request.method == "POST":
        form = DispositivoForm(request.POST)

        if form.is_valid():
            dispositivo = form.save(commit=False)

            # Generar credencial única para el dispositivo
            credencial = secrets.token_urlsafe(32)

            # Guardar únicamente el hash en la base de datos
            dispositivo.credencial_hash = make_password(credencial)

            dispositivo.save()

            return render(
                request,
                "appMovil/dispositivos/credencial.html",
                {
                    "dispositivo": dispositivo,
                    "credencial": credencial,
                }
            )

    else:
        form = DispositivoForm()

    return render(
        request,
        "appMovil/dispositivos/registrar_dispositivo.html",
        {
            "form": form
        }
    )

@login_required
def lista_dispositivos(request):
    dispositivos = Dispositivo.objects.select_related("repartidor").all()

    return render(
        request,
        "appMovil/dispositivos/lista_dispositivos.html",
        {
            "dispositivos": dispositivos
        }
    )


@login_required
def editar_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

    if request.method == "POST":
        form = DispositivoForm(request.POST, instance=dispositivo)

        if form.is_valid():
            form.save()

            return redirect("lista_dispositivos")

    else:
        form = DispositivoForm(instance=dispositivo)

    return render(
        request,
        "appMovil/dispositivos/editar.html",
        {
            "form": form,
            "dispositivo": dispositivo
        }
    )

@login_required
def activar_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)
    dispositivo.activo = True
    dispositivo.save(update_fields=["activo"])
    #messages.success(request, f'Dispositivo {dispositivo.nombre} activado.')
    return redirect('lista_dispositivos')


@login_required
def desactivar_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)
    dispositivo.activo = False
    dispositivo.save(update_fields=["activo"])
    #messages.success(request, f'Dispositivo {dispositivo.nombre} desactivado.')
    return redirect('lista_dispositivos')


@login_required
def eliminar_dispositivo(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)

    if request.method == "POST":
        dispositivo.delete()

        return redirect("lista_dispositivos")

    return render(
        request,
        "appMovil/dispositivos/eliminar.html",
        {
            "dispositivo": dispositivo
        }
    )

@api_view(['POST'])
def activar_dispositivo_api(request):
    serializer=DispositivoActivacionSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {
            "succes":False,
            "message":"Datos invalidos",
            "errors":serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    codigo=serializer.validated_data["codigo"]
    credencial=serializer.validated_data["credencial"]

    try:
        dispositivo=Dispositivo.objects.get(codigo=codigo)
    except Dispositivo.DoesNotExist:
        return Response(
            {
                "success":False,
                "message":"Dispositivo no encontrado",
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if not dispositivo.activo:
        return Response(
            {
                "success": False,
                "message": "El dispositivo se encuentra inactivo."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    if not check_password(credencial,dispositivo.credencial_hash):
        return Response(
            {
            "success":False,
            "message":"Credencial incorrecta"
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    dispositivo.ultima_conexion=timezone.now()
    dispositivo.save(update_fields=["ultima_conexion"])

    return Response(
        {
            "success":True,
            "message":"Dispositivo activado correctamente"
        },
        status=status.HTTP_200_OK
    )


@login_required
def dashboard_repartidor_api(request):

    repartidor = request.user

    # =========================
    # RUTA
    # =========================
    ruta = Ruta.objects.filter(
        usuario=repartidor,
        estado=True
    ).select_related(
        'vehiculo'
    ).first()

    if not ruta:
        return JsonResponse({
            'success': False,
            'mensaje': 'No tienes una ruta asignada.'
        })

    # =========================
    # MINIBODEGA
    # =========================
    minibodega = MiniBodega.objects.filter(
        ruta=ruta
    ).select_related(
        'vehiculo'
    ).first()

    # =========================
    # INVENTARIO
    # =========================
    inventario = []

    if minibodega:

        detalles = MiniBodegaDetalle.objects.filter(
            mini_bodega=minibodega
        ).select_related(
            'producto_variacion__producto',
            'producto_variacion__presentacion'
        )

        for detalle in detalles:

            inventario.append({
                'producto': detalle.producto_variacion.producto.nombre,
                'presentacion': detalle.producto_variacion.presentacion.nombre,
                'cantidad_inicial': detalle.cantidad_inicial,
                'cantidad_actual': detalle.cantidad_actual,
            })

    # =========================
    # FECHA ACTUAL
    # =========================
    hoy = timezone.localdate()

    # =========================
    # VENTAS DEL DÍA
    # =========================
    ventas_hoy = Venta.objects.filter(
        usuario=repartidor,
        fecha__date=hoy
    )

    cantidad_ventas = ventas_hoy.count()

    dinero_ventas = ventas_hoy.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')

    # =========================
    # VENTAS DE CONTADO
    # =========================
    ventas_contado = ventas_hoy.filter(
        tipo_venta='CONTADO'
    ).aggregate(
        total=Sum('total')
    )['total'] or Decimal('0.00')

    # =========================
    # ABONOS DEL DÍA
    # =========================
    abonos_hoy = Abono.objects.filter(
        usuario=repartidor,
        fecha__date=hoy
    )

    cantidad_abonos = abonos_hoy.count()

    dinero_abonos = abonos_hoy.aggregate(
        total=Sum('monto')
    )['total'] or Decimal('0.00')

    # =========================
    # DEVOLUCIONES DEL DÍA
    # =========================
    devoluciones_hoy = Devolucion.objects.filter(
        usuario=repartidor,
        fecha__date=hoy
    )

    cantidad_devoluciones = devoluciones_hoy.count()

    dinero_devoluciones = DevolucionDetalle.objects.filter(
        devolucion__in=devoluciones_hoy
    ).aggregate(
        total=Sum(
            F('cantidad') * F('precio_unitario')
        )
    )['total'] or Decimal('0.00')

    # =========================
    # EFECTIVO ESPERADO
    # =========================
    efectivo_esperado = (
        ventas_contado +
        dinero_abonos
    )

    # =========================
    # RESPUESTA
    # =========================
    return JsonResponse({

        'success': True,

        'repartidor': {
            'nombre': f'{repartidor.first_name} {repartidor.last_name}',
        },

        'ruta': {
            'id': ruta.id,
            'nombre': ruta.nombre,
        },

        'vehiculo': {
            'marca': ruta.vehiculo.marca,
            'placa': ruta.vehiculo.placa,
        },

        'minibodega': {
            'id': minibodega.id if minibodega else None,
            'estado': minibodega.estado if minibodega else None,
        },

        'inventario': inventario,

        'jornada': {
            'fecha': hoy.strftime('%Y-%m-%d'),

            'ventas': {
                'cantidad': cantidad_ventas,
                'dinero': float(dinero_ventas),
            },

            'abonos': {
                'cantidad': cantidad_abonos,
                'dinero': float(dinero_abonos),
            },

            'devoluciones': {
                'cantidad': cantidad_devoluciones,
                'dinero': float(dinero_devoluciones),
            },

            'efectivo_esperado': float(efectivo_esperado),
        }
    })