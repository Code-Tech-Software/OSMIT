from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from ProductoGranel.models import User, PedidoProduccion
from appMovil.models import MiniBodega, MiniBodegaDetalle, PedidoReabastecimiento
from . import models
from .forms import ProductoTerminadoForm, EntradaForm, ProductoVariacionForm
from .models import ProductoTerminado, EntradaPTerminado, DetalleEntradaPTerminado, ProductoVariacion, InventarioRuta
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .forms import SalidaForm
from .models import ProductoTerminado, SalidaPTerminado, DetalleSalidaPTerminado
from decimal import Decimal, InvalidOperation
from django.contrib.messages import get_messages
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import csv
import datetime
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import Sum
from .models import DetalleSalidaPTerminado, ProductoTerminado
from django.forms import inlineformset_factory
from django.db import transaction
from .forms import ProductoVariacionBaseFormSet
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ProductoTerminado
from .forms import ProductoTerminadoForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render




@login_required
@transaction.atomic
def agregar_producto(request):
    # Definimos el formset
    ProductoVariacionFormSet = inlineformset_factory(
        ProductoTerminado,
        ProductoVariacion,
        form=ProductoVariacionForm,
        formset=ProductoVariacionBaseFormSet,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        form = ProductoTerminadoForm(request.POST, request.FILES)
        # BUG SOLUCIONADO: Faltaba request.FILES para las imágenes de las variaciones
        formset = ProductoVariacionFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            # 1. Guardamos el producto base
            producto = form.save()

            # 2. BUG SOLUCIONADO: Vinculamos el formset a la instancia del producto padre
            formset.instance = producto

            # 3. Guardamos las variaciones (Django maneja las eliminaciones automáticamente aquí)
            variaciones = formset.save()

            # 4. Generamos las entradas automáticas de stock
            for variacion in variaciones:
                if variacion.stock > 0:
                    entrada = EntradaPTerminado.objects.create(
                        fecha_entrada=timezone.now(),
                        usuario=request.user,
                        nota=f"Entrada automática por variación: {producto.nombre}"
                    )

                    DetalleEntradaPTerminado.objects.create(
                        entrada_p_terminado=entrada,
                        producto_variacion=variacion,
                        cantidad=variacion.stock
                    )

            messages.success(request, "Producto y variaciones agregados correctamente.")
            return redirect('listar_productosPT')
        else:
            if formset.non_form_errors():
                for error in formset.non_form_errors():
                    messages.error(request, error)
            if formset.errors:
                messages.error(request, "Hay errores en los campos de las variaciones.")
            if form.errors:
                messages.error(request, "Error en los datos generales del producto.")

    else:
        form = ProductoTerminadoForm()
        formset = ProductoVariacionFormSet()

    return render(
        request,
        'ProductoTerminado/entradas/agregar_producto.html',
        {'form': form, 'formset': formset}
    )


@login_required
def listar_productos(request):
    """
    Muestra un listado agrupado con todas las variaciones de productos
    terminados registrados respetando el switch de estado.
    """
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    # Agregamos .order_by('producto__nombre') para poder agrupar en el template
    queryset = ProductoVariacion.objects.select_related(
        'producto',
        'presentacion'
    ).order_by('producto__nombre')

    if mostrar_todos:
        variaciones = queryset.all()
    else:
        # Filtramos basándonos en el estado del producto padre
        variaciones = queryset.filter(producto__estado=True)

    return render(request, 'ProductoTerminado/productos/listar_productos.html', {
        'variaciones': variaciones,
        'mostrar_todos': mostrar_todos
    })

@login_required
def editar_producto(request, pk):
    """
    Permite editar un producto existente y sus variaciones.
    """
    producto = get_object_or_404(ProductoTerminado, pk=pk)

    # Creamos el formset asociando el producto con sus variaciones
    VariacionFormSet = inlineformset_factory(
        ProductoTerminado,
        ProductoVariacion,
        form=ProductoVariacionForm,
        formset=ProductoVariacionBaseFormSet,
        extra=0,  # No mostramos filas vacías por defecto, las agregaremos con JS
        can_delete=True  # Habilita la opción de eliminar variaciones existentes
    )

    if request.method == 'POST':
        form = ProductoTerminadoForm(request.POST, request.FILES, instance=producto)
        formset = VariacionFormSet(request.POST, instance=producto)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Producto y variaciones actualizados correctamente.")
            return redirect('listar_productosPT')

        else:
            # ESTO ES NUEVO: Avisar al usuario que hay errores
            messages.error(request, "No se pudo guardar. Por favor, revisa los errores.")
    else:
        form = ProductoTerminadoForm(instance=producto)
        formset = VariacionFormSet(instance=producto)

    return render(request, 'ProductoTerminado/productos/editar_producto.html', {
        'form': form,
        'formset': formset
    })
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


@login_required
def registrar_entrada(request):

    productos = ProductoTerminado.objects.filter(estado=True).prefetch_related('variaciones',                                                                         'variaciones__presentacion')
    presentaciones = PresentacionProductoTerminado.objects.filter(estado=True)

    if request.method == 'POST':
        form = EntradaForm(request.POST)
        if form.is_valid():
            nota = form.cleaned_data.get('nota', '')
            detalles_validos = []
            for key, value in request.POST.items():
                if key.startswith('cantidad_'):
                    try:
                        variacion_id = int(key.split('_')[1])
                        cantidad = Decimal(value)

                        if cantidad > 0:
                            variacion = ProductoVariacion.objects.get(id=variacion_id)
                            detalles_validos.append((variacion, cantidad))
                    except (ValueError, TypeError, ProductoVariacion.DoesNotExist):
                        continue

            if detalles_validos:
                try:
                    with transaction.atomic():
                        entrada = EntradaPTerminado.objects.create(
                            fecha_entrada=timezone.now(),
                            usuario=request.user,
                            nota=nota
                        )
                        for variacion, cantidad in detalles_validos:
                            DetalleEntradaPTerminado.objects.create(
                                entrada_p_terminado=entrada,
                                producto_variacion=variacion,
                                cantidad=cantidad
                            )
                            variacion.stock += cantidad
                            variacion.save()

                    messages.success(request, 'Entrada registrada correctamente.')
                    return redirect('registrar_entradaPT')
                except Exception as e:
                    messages.error(request, f'Error al registrar la entrada: {str(e)}')
            else:
                messages.error(request, 'Debe ingresar al menos una cantidad mayor a 0.')
    else:
        form = EntradaForm()

    productos_matriz = []

    for prod in productos:
        vars_dict = {var.presentacion.id: var for var in prod.variaciones.all()}
        if not vars_dict:
            continue

        celdas = []
        for pres in presentaciones:
            variacion = vars_dict.get(pres.id)
            if variacion:
                celdas.append({
                    'existe': True,
                    'variacion_id': variacion.id,
                    'stock': variacion.stock,
                    'stock_min': variacion.stock_min,
                    'nombre_presentacion': str(pres)
                })
            else:
                celdas.append({'existe': False})

        productos_matriz.append({
            'producto': prod,
            'celdas': celdas
        })

    return render(request, 'ProductoTerminado/entradas/registrar_entrada.html', {
        'form': form,
        'presentaciones': presentaciones,
        'productos_matriz': productos_matriz
    })




@login_required
def registrar_salida(request):
    productos = ProductoTerminado.objects.filter(estado=True).prefetch_related(
        'variaciones', 'variaciones__presentacion'
    )
    presentaciones = PresentacionProductoTerminado.objects.filter(estado=True)

    if request.method == 'POST':
        form = SalidaForm(request.POST)
        if form.is_valid():
            ruta = form.cleaned_data.get('ruta')
            destino = form.cleaned_data.get('destino')
            nota = form.cleaned_data.get('nota', '')

            # 1. Validación estricta: Si el destino es "Ruta" (opcion1), la ruta es obligatoria
            if destino == 'opcion1' and not ruta:
                messages.error(request, 'Debes seleccionar una Ruta específica cuando el destino es "Ruta".')
            else:
                detalles_validos = []
                errores_stock = []

                # 2. Recopilar cantidades y validar stock
                for key, value in request.POST.items():
                    if key.startswith('cantidad_'):
                        try:
                            variacion_id = int(key.split('_')[1])
                            cantidad = Decimal(value)

                            if cantidad > 0:
                                variacion = ProductoVariacion.objects.select_for_update().get(id=variacion_id)

                                # Validar que no salga más del stock disponible
                                if cantidad > variacion.stock:
                                    errores_stock.append(
                                        f"{variacion.producto.nombre} ({variacion.presentacion}): Solicitado {cantidad}, Disponible {variacion.stock}"
                                    )
                                else:
                                    detalles_validos.append((variacion, cantidad))
                        except (ValueError, TypeError, ProductoVariacion.DoesNotExist):
                            continue

                if errores_stock:
                    for error in errores_stock:
                        messages.error(request, f'Stock insuficiente - {error}')
                elif not detalles_validos:
                    messages.error(request, 'Debe ingresar al menos una cantidad mayor a 0.')
                else:
                    try:
                        # 3. Transacción Atómica: Todo o nada
                        with transaction.atomic():
                            # A. Crear el registro principal de la salida
                            salida = SalidaPTerminado.objects.create(
                                fecha_salida=timezone.now(),
                                usuario=request.user,
                                ruta=ruta if destino == 'opcion1' else None,
                                destino=destino,
                                nota=nota
                            )

                            # Variables para MiniBodega si aplica
                            minibodega = None
                            if destino == 'opcion1' and ruta:
                                hoy = timezone.now().date()
                                # Buscar minibodega de la ruta de hoy, si no existe, la crea
                                minibodega, created = MiniBodega.objects.get_or_create(
                                    ruta=ruta,
                                    fecha=hoy,
                                    defaults={
                                        'usuario': request.user,
                                        # Asegúrate que tu modelo MiniBodega acepte la instancia de request.user
                                        'vehiculo': ruta.vehiculo,
                                        'estado': True
                                    }
                                )

                            # B. Registrar los detalles y mover el stock
                            for variacion, cantidad in detalles_validos:
                                # Descontar del stock principal
                                DetalleSalidaPTerminado.objects.create(
                                    salida_p_terminado=salida,
                                    producto_variacion=variacion,
                                    cantidad=cantidad
                                )
                                variacion.stock -= cantidad
                                variacion.save()

                                # C. Si el destino es la ruta, cargar a la MiniBodegaDetalle
                                if minibodega:
                                    mb_detalle, created_mb = MiniBodegaDetalle.objects.get_or_create(
                                        mini_bodega=minibodega,
                                        producto_variacion=variacion,
                                        defaults={
                                            'cantidad_inicial': Decimal('0.00'),
                                            'cantidad_actual': Decimal('0.00')
                                        }
                                    )
                                    # Se suma a lo que ya tuviera en la ruta ese día
                                    mb_detalle.cantidad_inicial += cantidad
                                    mb_detalle.cantidad_actual += cantidad
                                    mb_detalle.save()

                        messages.success(request, 'Salida registrada y stock actualizado correctamente.')
                        return redirect('registrar_salidaPT')  # <- Asegura que sea tu url real

                    except Exception as e:
                        messages.error(request, f'Error crítico al registrar la salida: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = SalidaForm()

    # Construir la matriz de productos
    productos_matriz = []
    for prod in productos:
        vars_dict = {var.presentacion.id: var for var in prod.variaciones.all()}
        if not vars_dict:
            continue

        celdas = []
        for pres in presentaciones:
            variacion = vars_dict.get(pres.id)
            if variacion:
                celdas.append({
                    'existe': True,
                    'variacion_id': variacion.id,
                    'stock': variacion.stock,
                    'stock_min': variacion.stock_min,
                    'nombre_presentacion': str(pres)
                })
            else:
                celdas.append({'existe': False})

        productos_matriz.append({
            'producto': prod,
            'celdas': celdas
        })

    return render(request, 'ProductoTerminado/salidas/registrar_salida.html', {
        'form': form,
        'presentaciones': presentaciones,
        'productos_matriz': productos_matriz
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




# PARA EL DASSBOAR



# Graficas prueba#

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from .models import  ProductoTerminado
from django.utils.timezone import now, timedelta



@api_view(['GET'])
def stock_productos(request):
    data = list(ProductoTerminado.objects.values(
        'nombre', 'stock', 'stock_min'
    ))
    return Response(data)


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


def api_indicadores_pt(request):
    total_productos = ProductoVariacion.objects.filter(producto__estado=True).count()
    productos_bajo_min = ProductoVariacion.objects.filter(
        producto__estado=True,
        stock__lte=F('stock_min'),
        stock__gt=0
    ).count()
    productos_sin_stock = ProductoVariacion.objects.filter(
        producto__estado=True,
        stock__lte=0
    ).count()
    pedidos_pendientes = PedidoReabastecimiento.objects.filter(estado=True).count()
    data = {
        "total_productos": total_productos,
        "productos_bajo_min": productos_bajo_min,
        "productos_sin_stock": productos_sin_stock,
        "pedidos_pendientes": pedidos_pendientes
    }

    return JsonResponse(data)


