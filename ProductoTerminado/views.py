from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from ProductoGranel.models import User, PedidoProduccion
from . import models
from .forms import ProductoTerminadoForm, EntradaForm, CorteInventarioPTerminadoForm, GramajeProductoTerminadoForm
from .models import ProductoTerminado, EntradaPTerminado, DetalleEntradaPTerminado, CorteInventarioPTerminado, \
    DetalleCorteInventarioPTerminado, GramajeProductoTerminado, VentaCliente
from decimal import Decimal
from django.contrib import messages

from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from .forms import SalidaForm
from .models import ProductoTerminado, SalidaPTerminado, DetalleSalidaPTerminado
from decimal import Decimal, InvalidOperation
from django.contrib.messages import get_messages


@login_required
def agregar_producto(request):
    """
    Vista para agregar un nuevo ProductoTerminado. Si el producto tiene stock (>0),
    se crea una EntradaPTerminado y un DetalleEntradaPTerminado para ese producto.
    """
    if request.method == 'POST':
        form = ProductoTerminadoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            # Si se registró stock, se crea la entrada
            if producto.stock > 0:
                entrada = EntradaPTerminado.objects.create(
                    fecha_entrada=timezone.now(),
                    usuario=request.user,
                    nota=f"Entrada automática por agregar producto: {producto.nombre}"
                )
                DetalleEntradaPTerminado.objects.create(
                    entrada_p_terminado=entrada,
                    producto_terminado=producto,
                    cantidad=producto.stock
                )
            messages.success(request, "Producto agregado correctamente.")
            return redirect('listar_productosPT')
    else:
        form = ProductoTerminadoForm()
    return render(request, 'ProductoTerminado/entradas/agregar_producto.html', {'form': form})


@login_required
def registrar_entrada(request):
    productos = ProductoTerminado.objects.filter(estado=True)

    if request.method == 'POST':
        form = EntradaForm(request.POST)
        if form.is_valid():
            nota = form.cleaned_data.get('nota', '')
            detalles_validos = []

            for producto in productos:
                campo = f'cantidad_{producto.id}'
                cantidad = request.POST.get(campo)
                try:
                    cantidad = float(cantidad)
                except (TypeError, ValueError):
                    cantidad = 0
                if cantidad > 0:
                    detalles_validos.append((producto, cantidad))

            if detalles_validos:
                entrada = EntradaPTerminado.objects.create(
                    fecha_entrada=timezone.now(),
                    usuario=request.user,
                    nota=nota
                )
                for producto, cantidad in detalles_validos:
                    DetalleEntradaPTerminado.objects.create(
                        entrada_p_terminado=entrada,
                        producto_terminado=producto,
                        cantidad=cantidad
                    )
                    producto.stock += Decimal(cantidad)
                    producto.save()

                messages.success(request, 'Entrada registrada correctamente.')
                return redirect('registrar_entradaPT')
            else:
                messages.error(request, 'Debe ingresar al menos una cantidad mayor a 0.')
    else:
        form = EntradaForm()

    return render(request, 'ProductoTerminado/entradas/registrar_entrada.html', {
        'form': form,
        'productos': productos
    })


@login_required
def registrar_salida(request):
    productos = ProductoTerminado.objects.filter(estado=True)
    detalles_validos = []

    if request.method == 'POST':
        salida_form = SalidaForm(request.POST)
        if salida_form.is_valid():
            for producto in productos:
                campo = f'cantidad_{producto.id}'
                cantidad_input = request.POST.get(campo)
                try:
                    cantidad = Decimal(cantidad_input)
                except (TypeError, ValueError, InvalidOperation):
                    cantidad = Decimal('0')

                if cantidad > 0:
                    if producto.stock >= cantidad:
                        detalles_validos.append((producto, cantidad))
                    else:
                        messages.error(request, f"El producto '{producto.nombre}' no tiene stock suficiente.")

            if not detalles_validos and not get_messages(request):
                messages.error(request, "Debe ingresar al menos una cantidad mayor a 0.")
            # Si hubo errores, simplemente renderizamos el template sin redireccionar
            if messages.get_messages(request):
                return render(request, 'ProductoTerminado/salidas/registrar_salida.html', {
                    'salida_form': salida_form,
                    'productos': productos,
                })

            # Guardamos la salida si todo es válido
            salida = salida_form.save(commit=False)
            salida.fecha_salida = timezone.now()
            salida.usuario = request.user
            salida.save()

            for producto, cantidad in detalles_validos:
                DetalleSalidaPTerminado.objects.create(
                    salida_p_terminado=salida,
                    producto_terminado=producto,
                    cantidad=cantidad
                )
                producto.stock -= cantidad
                producto.save()

            messages.success(request, "Salida registrada exitosamente.")
            return redirect('registrar_salidaPT')
    else:
        salida_form = SalidaForm()

    return render(request, 'ProductoTerminado/salidas/registrar_salida.html', {
        'salida_form': salida_form,
        'productos': productos,
    })


###==========================================

@login_required
def ajustar_inventario_corte(request, pk):
    """
    Toma un CorteInventarioPTerminado pendiente, recorre sus DetalleCorteInventarioPTerminado
    y:
      - si diferencia > 0 → crea (o añade) DetalleEntradaPTerminado y actualiza stock +
      - si diferencia < 0 → crea (o añade) DetalleSalidaPTerminado y actualiza stock –
    Finalmente marca el corte como 'ajustado'.
    """
    corte = get_object_or_404(CorteInventarioPTerminado, pk=pk)
    detalles = corte.detallecorteinventariopterminado_set.filter(ajuste_necesario=True)

    if not detalles.exists():
        messages.info(request, "No hay ajustes necesarios en este corte.")
        return redirect('detalle_corte_producto_terminado', pk=corte.pk)

    entrada = None
    salida = None

    for d in detalles:
        diff = d.diferencia
        prod = d.producto_terminado

        if diff > 0:
            # necesito una entrada para subir stock
            if entrada is None:
                entrada = EntradaPTerminado.objects.create(
                    fecha_entrada=timezone.now(),
                    usuario=request.user,
                    nota=f"Ajuste automático corte #{corte.id}"
                )
            DetalleEntradaPTerminado.objects.create(
                entrada_p_terminado=entrada,
                producto_terminado=prod,
                cantidad=diff
            )
            prod.stock += diff
            prod.save()

        elif diff < 0:
            # necesito una salida para bajar stock
            cant = abs(diff)
            if salida is None:
                salida = SalidaPTerminado.objects.create(
                    fecha_salida=timezone.now(),
                    usuario=request.user,
                    nota=f"Ajuste automático corte #{corte.id}"
                )
            DetalleSalidaPTerminado.objects.create(
                salida_p_terminado=salida,
                producto_terminado=prod,
                cantidad=cant
            )
            prod.stock -= cant
            prod.save()

    corte.estado = 'ajustado'
    corte.save()

    messages.success(request, "Inventario ajustado y corte marcado como 'ajustado'.")
    return redirect('detalle_corte_producto_terminado', pk=corte.pk)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ProductoTerminado
from .forms import ProductoTerminadoForm


@login_required
def listar_productos(request):
    """
      Muestra un listado con todos los productos a granel registrados respetando el swich.
      """
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        productos = ProductoTerminado.objects.all()
    else:
        productos = ProductoTerminado.objects.filter(estado=True)

    return render(request, 'ProductoTerminado/productos/listar_productos.html',
                  {'productos': productos, 'mostrar_todos': mostrar_todos})


@login_required
def editar_producto(request, pk):
    """
    Permite editar un producto existente.
    """
    producto = get_object_or_404(ProductoTerminado, pk=pk)
    if request.method == 'POST':
        form = ProductoTerminadoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")  # esto para las notificaciones
            return redirect('listar_productosPT')
    else:
        form = ProductoTerminadoForm(instance=producto)
    return render(request, 'ProductoTerminado/productos/editar_producto.html', {'form': form})


@login_required
def eliminar_producto(request, pk):
    """
    Elimina lógicamente un producto cambiando su estado a False.
    """
    producto = get_object_or_404(ProductoTerminado, pk=pk)
    producto.estado = False
    producto.save()
    messages.success(request, "Producto desactivado correctamente.")
    return redirect('listar_productosPT')


# --------------------------------------

@login_required
def realizar_corte_producto_terminado(request):
    productos = ProductoTerminado.objects.filter(estado=True)
    if request.method == "POST":
        form = CorteInventarioPTerminadoForm(request.POST)
        if form.is_valid():
            corte = form.save(commit=False)
            corte.usuario = request.user
            corte.fecha = timezone.now()
            # Asumimos correcto si no hay diferencias
            corte.estado = 'correcto'
            corte.save()

            requiere_ajuste = False
            for producto in productos:
                stock_teorico = producto.stock
                stock_real_str = request.POST.get(f'stock_real_{producto.id}', '0')
                try:
                    stock_real = Decimal(stock_real_str)
                except:
                    stock_real = Decimal('0')
                diferencia = stock_real - stock_teorico
                ajuste = diferencia != 0
                if ajuste:
                    requiere_ajuste = True

                DetalleCorteInventarioPTerminado.objects.create(
                    corte_inventario_p_terminado=corte,
                    producto_terminado=producto,
                    stock_teorico=stock_teorico,
                    stock_real=stock_real,
                    diferencia=diferencia,
                    ajuste_necesario=ajuste
                )

            if requiere_ajuste:
                corte.estado = 'pendiente'
                corte.save()

            messages.success(request, "Corte de inventario de productos terminados registrado correctamente.")
            return redirect('lista_cortes_producto_terminado')
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = CorteInventarioPTerminadoForm()

    return render(request, 'ProductoTerminado/cortes/realizar_corte.html', {
        'form': form,
        'productos': productos,
    })


@login_required
def lista_cortes_producto_terminado(request):
    cortes = CorteInventarioPTerminado.objects.all().order_by('-fecha')
    return render(request, 'ProductoTerminado/cortes/lista_cortes.html', {
        'cortes': cortes,
    })


@login_required
def detalle_corte_producto_terminado(request, pk):
    corte = get_object_or_404(CorteInventarioPTerminado, pk=pk)
    detalles = DetalleCorteInventarioPTerminado.objects.filter(
        corte_inventario_p_terminado=corte
    )
    return render(request, 'ProductoTerminado/cortes/detalle_corte.html', {
        'corte': corte,
        'detalles': detalles,
    })


# View de Presentacio de productos terminados----------------------------------------#

from django.shortcuts import render, redirect, get_object_or_404
from .models import PresentacionProductoTerminado
from .forms import PresentacionProductoTerminadoForm


def lista_presentaciones(request):
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        presentaciones = PresentacionProductoTerminado.objects.all()
    else:
        presentaciones = PresentacionProductoTerminado.objects.filter(estado=True)

    return render(request, 'ProductoTerminado/presentaciones/lista.html',
                  {'presentaciones': presentaciones, 'mostrar_todos': mostrar_todos})


def crear_presentacion(request):
    if request.method == 'POST':
        form = PresentacionProductoTerminadoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Presentación creada correctamente.")
            return redirect('lista_presentaciones')
    else:
        form = PresentacionProductoTerminadoForm()
    return render(request, 'ProductoTerminado/presentaciones/crear.html', {'form': form})


def editar_presentacion(request, pk):
    presentacion = get_object_or_404(PresentacionProductoTerminado, pk=pk)
    form = PresentacionProductoTerminadoForm(request.POST or None, request.FILES or None, instance=presentacion)
    if form.is_valid():
        form.save()
        messages.success(request, "Presentación actualizada correctamente.")
        return redirect('lista_presentaciones')
    return render(request, 'ProductoTerminado/presentaciones/editar.html', {'form': form, 'presentacion': presentacion})


def eliminar_presentacion(request, pk):
    presentacion = get_object_or_404(PresentacionProductoTerminado, pk=pk)
    presentacion.estado = False
    presentacion.save()
    messages.success(request, "Presentación desactivada correctamente.")
    return redirect('lista_presentaciones')


# VISTAS PARA GRAMAJE  DE PRODUCTOS TERMINADOS


def lista_gramajes(request):
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        gramajes = GramajeProductoTerminado.objects.all()
    else:
        gramajes = GramajeProductoTerminado.objects.filter(estado=True)

    return render(request, 'ProductoTerminado/gramajes/lista.html',
                  {'gramajes': gramajes, 'mostrar_todos': mostrar_todos})


def crear_gramaje(request):
    if request.method == 'POST':
        form = GramajeProductoTerminadoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Gramaje creado correctamente.")
            return redirect('lista_gramajes')
    else:
        form = GramajeProductoTerminadoForm()
    return render(request, 'ProductoTerminado/gramajes/crear.html', {'form': form})


def editar_gramaje(request, pk):
    gramaje = get_object_or_404(GramajeProductoTerminado, pk=pk)
    form = GramajeProductoTerminadoForm(request.POST or None, request.FILES or None, instance=gramaje)
    if form.is_valid():
        form.save()
        messages.success(request, "Gramaje actualizado correctamente.")
        return redirect('lista_gramajes')
    return render(request, 'ProductoTerminado/gramajes/editar.html', {'form': form, 'gramaje': gramaje})


def eliminar_gramaje(request, pk):
    gramaje = get_object_or_404(GramajeProductoTerminado, pk=pk)
    gramaje.estado = False
    gramaje.save()
    messages.success(request, "Gramaje desactivado correctamente.")
    return redirect('lista_gramajes')


# PARA EL DASSBOAR


from django.db.models import F


def indicadores_producto_terminado(request):
    productos_activos = ProductoTerminado.objects.filter(estado=True)

    total_productos = productos_activos.count()

    productos_bajo_min = productos_activos.filter(
        stock__lt=F('stock_min'),
        stock__gt=0
    ).count()

    productos_sin_stock = productos_activos.filter(stock=0).count()
    pedidos_pendientes = VentaCliente.objects.filter(estado='pendiente').count()

    # Valor total del stock (stock * costo), solo para productos activos
    productos_con_valor = productos_activos.annotate(
        valor_total=ExpressionWrapper(
            F('stock') * F('precio'),
            output_field=DecimalField()
        )
    )
    valor_total_stock = productos_con_valor.aggregate(total=Sum('valor_total'))['total'] or 0

    return JsonResponse({
        'total_productos': total_productos,
        'productos_bajo_min': productos_bajo_min,
        'productos_sin_stock': productos_sin_stock,
        'pedidos_pendientes': pedidos_pendientes,
        'valor_total_stock': valor_total_stock,
    })


# Graficas prueba#

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from .models import DetalleVentaCliente, ProductoTerminado, DetalleCorteInventarioPTerminado, VentaCliente
from django.utils.timezone import now, timedelta


@api_view(['GET'])
def ventas_por_dia(request):
    desde = now() - timedelta(days=7)
    ventas = (VentaCliente.objects
              .filter(fecha_venta__gte=desde)
              .extra({'dia': "date(fecha_venta)"})
              .values('dia')
              .annotate(total=Sum('detalleventacliente__cantidad')))
    return Response(list(ventas))


@api_view(['GET'])
def productos_mas_vendidos(request):
    top = (DetalleVentaCliente.objects
           .values('producto_terminado__nombre')
           .annotate(total=Sum('cantidad'))
           .order_by('-total')[:5])
    return Response(list(top))


@api_view(['GET'])
def stock_productos(request):
    data = list(ProductoTerminado.objects.values(
        'nombre', 'stock', 'stock_min'
    ))
    return Response(data)


@api_view(['GET'])
def diferencias_inventario(request):
    data = list(DetalleCorteInventarioPTerminado.objects.values(
        'producto_terminado__nombre', 'diferencia'
    ))
    return Response(data)


# listado de salidas
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

from django.views.generic import ListView


class SalidaPTerminadoListView(ListView):
    model = SalidaPTerminado
    template_name = 'ProductoTerminado/salidas/lista_salidas.html'
    context_object_name = 'salidas'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().select_related('usuario', 'ruta')

        # Calculamos el total en dinero por salida
        queryset = queryset.annotate(
            total_dinero=Sum(
                ExpressionWrapper(
                    F('detallesalidapterminado__cantidad') * F('detallesalidapterminado__producto_terminado__precio'),
                    output_field=DecimalField()
                )
            )
        )

        ruta_id = self.request.GET.get('ruta')
        usuario_id = self.request.GET.get('usuario')
        destino = self.request.GET.get('destino')
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        dia = self.request.GET.get('dia')

        if ruta_id:
            queryset = queryset.filter(ruta_id=ruta_id)

        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        if destino:
            queryset = queryset.filter(destino=destino)

        if fecha_inicio and fecha_fin:
            queryset = queryset.filter(fecha_salida__date__range=(fecha_inicio, fecha_fin))

        elif dia:
            queryset = queryset.filter(fecha_salida__date=dia)

        return queryset.order_by('-fecha_salida')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Para poblar select dinámico

        from .models import Ruta

        context['rutas'] = Ruta.objects.all()
        context['usuarios'] = User.objects.all()
        context['DESTINO_CHOICES'] = dict(SalidaPTerminado.DESTINO_CHOICES)
        return context


from django.shortcuts import render
from .models import ProductoTerminado


def lista_productos_terminados(request):
    productos = ProductoTerminado.objects.filter(estado=True)
    return render(request, 'Produccion/lista_produccion_productoT.html', {'productos': productos})


# ''''''''''''''''''''''''''''''''''''''''''''PARA EL DASHBOARD Graficas

from datetime import timedelta
from django.utils.timezone import now
from django.db.models.functions import TruncDate
from django.http import JsonResponse


def entradas_salidas_por_dia_terminado(request):
    hoy = now().date()
    hace_7_dias = hoy - timedelta(days=6)
    dias = [hace_7_dias + timedelta(days=i) for i in range(7)]
    labels = [d.strftime("%d/%m") for d in dias]

    # Entradas por día (sumando cantidades)
    entradas = (
        DetalleEntradaPTerminado.objects
        .filter(entrada_p_terminado__fecha_entrada__date__range=(hace_7_dias, hoy))
        .annotate(fecha=TruncDate('entrada_p_terminado__fecha_entrada'))
        .values('fecha')
        .annotate(total=Sum('cantidad'))
        .order_by('fecha')
    )

    # Salidas por día (sumando cantidades)
    salidas = (
        DetalleSalidaPTerminado.objects
        .filter(salida_p_terminado__fecha_salida__date__range=(hace_7_dias, hoy))
        .annotate(fecha=TruncDate('salida_p_terminado__fecha_salida'))
        .values('fecha')
        .annotate(total=Sum('cantidad'))
        .order_by('fecha')
    )

    entradas_dict = {e['fecha']: float(e['total']) for e in entradas}
    salidas_dict = {s['fecha']: float(s['total']) for s in salidas}

    data_entradas = [entradas_dict.get(d, 0) for d in dias]
    data_salidas = [salidas_dict.get(d, 0) for d in dias]

    return JsonResponse({
        'labels': labels,
        'entradas': data_entradas,
        'salidas': data_salidas,
    })


def top_productos_mas_utilizados_terminado(request):
    hoy = now().date()
    hace_7_dias = hoy - timedelta(days=7)

    productos_top = (
        DetalleSalidaPTerminado.objects
        .filter(salida_p_terminado__fecha_salida__date__range=(hace_7_dias, hoy))
        .values('producto_terminado__nombre', 'producto_terminado__gramaje_producto_terminado__nombre')
        .annotate(total_salidas=Sum('cantidad'))
        .order_by('-total_salidas')[:5]
    )

    labels = [
        f"{item['producto_terminado__nombre']} ({item['producto_terminado__gramaje_producto_terminado__nombre']})"
        for item in productos_top
    ]
    data = [float(item['total_salidas']) for item in productos_top]

    return JsonResponse({
        'labels': labels,
        'data': data
    })


def indicadores_de_produccion(request):
    hoy = now().date()  # Fecha actual
    productos_activos = ProductoTerminado.objects.filter(estado=True)
    productos_bajo_min = productos_activos.filter(
        stock__lt=F('stock_min'),
        stock__gt=0
    ).count()
    productos_sin_stock = productos_activos.filter(stock=0).count()

    pedidos_pendientes = PedidoProduccion.objects.filter(estado='pendiente', fecha_pedido__date=hoy).count()

    pedidos_en_produccion = PedidoProduccion.objects.filter(estado='en_produccion', fecha_pedido__date=hoy).count()

    return JsonResponse({
        'productos_bajo_min': productos_bajo_min,
        'productos_sin_stock': productos_sin_stock,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_en_produccion': pedidos_en_produccion,

    })
