from datetime import datetime, timedelta
from django.shortcuts import render
from rest_framework import viewsets
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.timezone import make_aware, is_naive
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal


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