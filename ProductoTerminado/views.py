import decimal

from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from ProductoGranel.models import User, PedidoProduccion
from appMovil.models import MiniBodega, MiniBodegaDetalle, PedidoReabastecimiento
from . import models
from .forms import ProductoTerminadoForm, EntradaForm, ProductoVariacionForm
from .models import PresentacionProductoTerminado, ProductoTerminado, EntradaPTerminado, DetalleEntradaPTerminado, ProductoVariacion, CorreccionPTerminado
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
from .models import DetalleSalidaPTerminado, ProductoTerminado,CorteInventarioPTerminado,DetalleCorteInventarioPTerminado
from django.forms import inlineformset_factory
from django.db import transaction
from .forms import ProductoVariacionBaseFormSet, CorteInventarioPTerminadoForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ProductoTerminado
from .forms import ProductoTerminadoForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from django.urls import reverse
from Usuario.decorators import requiere_roles,solo_administrador
from django.views.decorators.http import require_POST
from django.db.models import Exists, OuterRef
import io
import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from xml.sax.saxutils import escape



@login_required
@requiere_roles("Producto Terminado")
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
@requiere_roles("Producto Terminado", "Recursos Humanos")
def listar_productos(request):
    """
    Muestra un listado agrupado con todas las variaciones de productos
    terminados, respetando los switches de estado y orden de ruta.
    """
    mostrar_todos = request.GET.get('mostrar_todos') == '1'
    usar_orden_personalizado = request.GET.get('orden') == 'personalizado'

    # =========================================================
    # ORDEN PERSONALIZADO DE PRODUCTOS
    # =========================================================
    orden_productos = [
        "PISTACHE", "ENCHILADO", "JAPONES", "JAPONES FUEGO", "MACHO",
        "HORNEADO", "CASCARITA", "SURTIDO", "HABA PELADA", "HABA CON CASCARA",
        "GARBANZA", "GARAPIÑADO", "GOMITA", "LUNETA", "HUEVITO CHOCOLATE",
        "GALLETA MARINA", "CIRUELA", "PASAS", "SEMILLA DE CALABAZA",
        "SEMILLA DE GIRASOL", "NUEZ", "ALMENDRA", "GRANOLA", "CHILE DE ARBOL",
        "CHILE PULLA", "CHILE CASCABEL", "CAMARON", "CAMARON MOLIDO",
        "CHARAL NATURAL", "CHARAL ADOBADO", "CECINA NATURAL", "CECINA ADOBADA",
        "CECINA DE LIMON", "CECINA CHILTEPIN", "CECINA CHIPOTLE",
        "CECINA HABANERO", "CECINA ARTESANAL", "PAPA FRITA",
        "CHURRO DE MASA", "CHURRO DELGADO", "CHICHARRON", "CHICHARRON CRAC",
        "PLATANO", "TOSTADA", "MIEL", "TIRA DE CC MINI", "TIRA DE DULCE",
        "MIX VERDE", "MIX ROJO"
    ]

    # =========================================================
    # ORDEN FIJO DE PRESENTACIONES
    # =========================================================
    orden_presentaciones = [
        "Minis", "Chico", "Mediano", "Grande", "250g", "500g",
        "1kg", "Kiosko", "Grande 150g", "Grande 140g", "Pieza"
    ]

    normalizar = lambda nombre: " ".join(nombre.upper().split())

    orden_productos_dict = {
        normalizar(nombre): i for i, nombre in enumerate(orden_productos)
    }
    orden_presentaciones_dict = {
        normalizar(nombre): i for i, nombre in enumerate(orden_presentaciones)
    }

    # =========================================================
    # CONSULTA DE VARIACIONES
    # =========================================================
    queryset = ProductoVariacion.objects.select_related(
        'producto', 'presentacion'
    ).order_by('producto__nombre')

    if mostrar_todos:
        variaciones = list(queryset.all())
    else:
        variaciones = list(queryset.filter(producto__estado=True))

    # =========================================================
    # ORDENAR PRODUCTOS Y PRESENTACIONES
    # =========================================================
    if usar_orden_personalizado:
        variaciones.sort(
            key=lambda item: (
                orden_productos_dict.get(normalizar(item.producto.nombre), 9999),
                normalizar(item.producto.nombre),
                item.producto.id,
                orden_presentaciones_dict.get(normalizar(item.presentacion.nombre), 9999),
                normalizar(item.presentacion.nombre)
            )
        )
    else:
        variaciones.sort(
            key=lambda item: (
                normalizar(item.producto.nombre),
                item.producto.id,
                orden_presentaciones_dict.get(normalizar(item.presentacion.nombre), 9999),
                normalizar(item.presentacion.nombre)
            )
        )

    return render(request, 'ProductoTerminado/productos/listar_productos.html', {
        'variaciones': variaciones,
        'mostrar_todos': mostrar_todos,
        'usar_orden_personalizado': usar_orden_personalizado
    })

from django.db.models import Case, When, Value, IntegerField

@login_required
@requiere_roles("Producto Terminado")
def editar_producto(request, pk):
    """
    Permite editar un producto existente y sus variaciones.
    """
    producto = get_object_or_404(ProductoTerminado, pk=pk)

    # =========================================================
    # ORDEN FIJO DE PRESENTACIONES
    # =========================================================
    orden_presentaciones = [
        "Minis", "Chico", "Mediano", "Grande", "250g", "500g",
        "1kg", "Kiosko", "Grande 150g", "Grande 140g", "Pieza"
    ]

    orden_case = Case(
        *[
            When(presentacion__nombre__iexact=nombre, then=Value(i))
            for i, nombre in enumerate(orden_presentaciones)
        ],
        default=Value(9999),
        output_field=IntegerField()
    )

    variaciones_ordenadas = ProductoVariacion.objects.filter(
        producto=producto
    ).order_by(
        orden_case,
        'presentacion__nombre',
        'id'
    )

    # =========================================================
    # FORMSET DE VARIACIONES
    # =========================================================
    VariacionFormSet = inlineformset_factory(
        ProductoTerminado,
        ProductoVariacion,
        form=ProductoVariacionForm,
        formset=ProductoVariacionBaseFormSet,
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        form = ProductoTerminadoForm(
            request.POST, request.FILES, instance=producto
        )
        formset = VariacionFormSet(
            request.POST,
            instance=producto,
            queryset=variaciones_ordenadas
        )

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(
                request,
                "Producto y variaciones actualizados correctamente."
            )
            return redirect('listar_productosPT')
        else:
            messages.error(
                request,
                "No se pudo guardar. Por favor, revisa los errores."
            )
    else:
        form = ProductoTerminadoForm(instance=producto)
        formset = VariacionFormSet(
            instance=producto,
            queryset=variaciones_ordenadas
        )

    return render(request, 'ProductoTerminado/productos/editar_producto.html', {
        'form': form,
        'formset': formset
    })

@login_required
@requiere_roles("Producto Terminado")
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
@requiere_roles("Producto Terminado")
def registrar_entrada(request):

    # =========================================================
    # PRESENTACIONES NORMALES
    # =========================================================
    presentaciones = PresentacionProductoTerminado.objects.filter(
        estado=True,
        nombre__in=[
            "Minis",
            "Chico",
            "Mediano",
            "Grande",
            "250g",
            "500g",
            "1kg",
            "Grande 150g",
            "Grande 140g",
            "Pieza",
            "Kiosko",
        ]
    )
    # Yeos 200 Yeos gnd Kiosko

    # =========================================================
    # PRODUCTOS NORMALES
    # Excluimos los que comienzan con los prefijos especiales
    # =========================================================
    productos = ProductoTerminado.objects.filter(
        estado=True
    ).exclude(
        Q(nombre__startswith="ML ") |
        Q(nombre__startswith="Y ") |
        Q(nombre__startswith="YML ") |
        Q(nombre__startswith="YV ") |
        Q(nombre__startswith="JP ") |
        Q(nombre__startswith="N ")
    ).prefetch_related(
        'variaciones',
        'variaciones__presentacion'
    )

    # =========================================================
    # ORDEN PERSONALIZADO DE PRODUCTOS
    # =========================================================
    orden_productos = [
        "PISTACHE", "ENCHILADO", "JAPONES", "JAPONES FUEGO", "MACHO",
        "HORNEADO", "CASCARITA", "SURTIDO", "HABA PELADA", "HABA CON CASCARA",
        "GARBANZA", "GARAPIÑADO", "GOMITA", "LUNETA", "HUEVITO CHOCOLATE",
        "GALLETA MARINA", "CIRUELA", "PASAS", "SEMILLA DE CALABAZA",
        "SEMILLA DE GIRASOL", "NUEZ", "ALMENDRA", "GRANOLA", "CHILE DE ARBOL",
        "CHILE PULLA", "CHILE CASCABEL", "CAMARON", "CAMARON MOLIDO",
        "CHARAL NATURAL", "CHARAL ADOBADO", "CECINA NATURAL", "CECINA ADOBADA",
        "CECINA DE LIMON", "CECINA CHILTEPIN", "CECINA CHIPOTLE",
        "CECINA HABANERO", "CECINA ARTESANAL", "PAPA FRITA",
        "CHURRO DE MASA", "CHURRO DELGADO", "CHICHARRON", "CHICHARRON CRAC",
        "PLATANO", "TOSTADA", "MIEL", "TIRA DE CC MINI", "TIRA DE DULCE",
        "MIX VERDE", "MIX ROJO"
    ]

    usar_orden_personalizado = request.GET.get('orden') == 'personalizado'

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

    # =========================================================
    # MATRIZ DE PRODUCTOS Y PRESENTACIONES
    # =========================================================
    productos_matriz = []

    for prod in productos:
        vars_dict = {
            var.presentacion.id: var
            for var in prod.variaciones.all()
        }

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
                celdas.append({
                    'existe': False
                })

        productos_matriz.append({
            'producto': prod,
            'celdas': celdas
        })

    # =========================================================
    # ORDENAR PRODUCTOS
    # =========================================================
    if usar_orden_personalizado:
        orden_dict = {
            nombre: i
            for i, nombre in enumerate(orden_productos)
        }

        productos_matriz.sort(
            key=lambda item: (
                orden_dict.get(
                    item['producto'].nombre.strip().upper(),
                    9999
                ),
                item['producto'].nombre
            )
        )
    else:
        productos_matriz.sort(
            key=lambda item: item['producto'].nombre
        )

    return render(
        request,
        'ProductoTerminado/entradas/registrar_entrada.html',
        {
            'form': form,
            'presentaciones': presentaciones,
            'productos_matriz': productos_matriz,
            'usar_orden_personalizado': usar_orden_personalizado
        }
    )


@login_required
@requiere_roles("Producto Terminado")
def registrar_entrada_especial  (request):
    ##Especiales disponibles

    especiales={
        "ML": {
            "nombre": "Mega Lupita",
            "presentaciones": [
                "250g",
                "230g",
                "60g",
                "50g",
                "150g",
                "40g",
                ]
        },
        "Y": {
            "nombre": "Yeos",
            "presentaciones": [
                "200g",
                "180g",
                "150g",
                "120g",
                "60g",
                "220g",
                "250g",
                "100g",
                "700g",
                "650g",
                ]
        },
        "YML": {
            "nombre": "Super la merced",
            "presentaciones": [
                "20g",
                "70g",
                "80g",
                "60g",
                "65g",
                "100g",
                "50g",
                "45g",
                "40g",
                "200g",
                "150g",
                "180g",
                "220g",
                "500g",
                ]
        },
        "YV": {
            "nombre": "Yeos Victoria",
            "presentaciones": [
                "200g",
                "180g",
                "150g",
                "220g",
                "60g",
                "100g",
                "250g",
                "700g",
                "650g",
                ]
        },
        "JP": {
            "nombre": "Juaquin Perez",
            "presentaciones": [
                "750g",
                "250g",
                "150g",
                ]
        },
        "N": {
            "nombre": "Norma",
            "presentaciones": [
                "620g",
                "600g",
                ]
        },
    }


    #Especial seleccionado

    especial_seleccionado = request.GET.get('especial', 'ML')  # Valor por defecto
    if especial_seleccionado not in especiales:
        especial_seleccionado = 'ML'  # Valor por defecto si no es válido

    especial = especiales[especial_seleccionado]

    nombres_presentaciones = especial["presentaciones"]



    ##Presentaciones

    presentaciones = PresentacionProductoTerminado.objects.filter(
        estado=True,
        nombre__in=nombres_presentaciones
    )

    # =========================================================
    # PRODUCTOS ESPECIALES
    # =========================================================

    productos = ProductoTerminado.objects.filter(
        estado=True,
        nombre__startswith=f"{especial_seleccionado} "
        )   .order_by('id').prefetch_related(
        'variaciones',
        'variaciones__presentacion')

    #Post

    if request.method == 'POST':
        form  = EntradaForm(request.POST)
        if form.is_valid():
            nota = form.cleaned_data.get('nota', '')
            detalles_validos = []

            for key, value in request.POST.items():
                if key.startswith('cantidad_'):
                    try:
                        variacion_id = int(key.split('_')[1])
                        cantidad = Decimal(value)

                        if cantidad > 0:
                            variacion = (
                                ProductoVariacion.objects.get(
                                    id=variacion_id,
                                    producto__nombre__startswith=(
                                        f"{especial_seleccionado} "
                                    ),
                                    presentacion__nombre__in=(
                                        nombres_presentaciones
                                    )
                                )
                            )

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
                    return redirect('registrar_entrada_especialPT')
                except Exception as e:
                    messages.error(request, f'Error al registrar la entrada: {str(e)}')
            else:
                messages.error(request, 'Debe ingresar al menos una cantidad mayor a 0.')
    else:
        form = EntradaForm()


    #Matriz de productos x Presentacion

    productos_matriz = []
    for prod in productos:

        vars_dict = {
            var.presentacion.id: var
            for var in prod.variaciones.all()
            if var.presentacion.nombre in nombres_presentaciones
        }

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

                celdas.append({
                    'existe': False
                })

        productos_matriz.append({
            'producto': prod,
            'celdas': celdas
        })

    return render(
        request,
        'ProductoTerminado/entradas/registrar_entrada_especial.html',
        {
            'form': form,
            'especiales': especiales,
            'especial_seleccionado': especial_seleccionado,
            'especial': especial,
            'presentaciones': presentaciones,
            'productos_matriz': productos_matriz,
        }
    )





from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# (Asegúrate de que tus modelos y formularios estén importados correctamente arriba)


from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


# (Asegúrate de que tus modelos y formularios estén importados correctamente)

@login_required
@requiere_roles("Producto Terminado")
def registrar_salida(request):
    # =========================================================
    # PRODUCTOS NORMALES
    # =========================================================
    productos = ProductoTerminado.objects.filter(
        estado=True
    ).exclude(
        Q(nombre__startswith="ML ") |
        Q(nombre__startswith="Y ") |
        Q(nombre__startswith="YML ") |
        Q(nombre__startswith="YV ") |
        Q(nombre__startswith="JP ") |
        Q(nombre__startswith="N ")
    ).order_by('id').prefetch_related(
        'variaciones',
        'variaciones__presentacion'
    )

    # =========================================================
    # PRESENTACIONES NORMALES
    # =========================================================
    presentaciones_qs = PresentacionProductoTerminado.objects.filter(
        estado=True,
        nombre__in=[
            "Minis", "Chico", "Mediano", "Grande", "250g", "500g",
            "1kg", "Grande 150g", "Grande 140g", "Pieza", "Kiosko"
        ]
    )

    orden_deseado = [
        "Chico", "Mediano", "Grande", "250g", "500g", "1kg",
        "Grande 150g", "Grande 140g", "Minis", "Kiosko"
    ]

    presentaciones = list(presentaciones_qs)

    presentaciones.sort(
        key=lambda p: orden_deseado.index(str(p))
        if str(p) in orden_deseado else 99
    )

    # =========================================================
    # ORDEN DE PRODUCTOS
    # =========================================================
    orden_productos = [
            "PISTACHE", "ENCHILADO", "JAPONES", "JAPONES FUEGO", "MACHO",
            "HORNEADO", "CASCARITA", "SURTIDO", "HABA PELADA", "HABA CON CASCARA",
            "GARBANZA", "GARAPIÑADO", "GOMITA", "LUNETA", "HUEVITO CHOCOLATE",
            "GALLETA MARINA", "CIRUELA", "PASAS", "SEMILLA DE CALABAZA",
            "SEMILLA DE GIRASOL", "NUEZ", "ALMENDRA", "GRANOLA", "CHILE DE ARBOL",
            "CHILE PULLA", "CHILE CASCABEL", "CAMARON", "CAMARON MOLIDO",
            "CHARAL NATURAL", "CHARAL ADOBADO", "CECINA NATURAL", "CECINA ADOBADA",
            "CECINA DE LIMON", "CECINA CHILTEPIN", "CECINA CHIPOTLE",
            "CECINA HABANERO", "CECINA ARTESANAL", "PAPA FRITA",
            "CHURRO DE MASA", "CHURRO DELGADO", "CHICHARRON", "CHICHARRON CRAC",
            "PLATANO", "TOSTADA", "MIEL", "TIRA DE CC MINI", "TIRA DE DULCE",
            "MIX VERDE", "MIX ROJO"
        ]

    usar_orden_personalizado = request.GET.get('orden') == 'personalizado'

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
                try:
                    # Todo dentro de atomic para que el select_for_update funcione
                    # y si algo falla, no se guarde nada a medias.
                    with transaction.atomic():
                        detalles_validos = []
                        errores_stock = []

                        # 2. Recopilar cantidades y validar stock
                        for key, value in request.POST.items():
                            if key.startswith('cantidad_'):
                                try:
                                    variacion_id = int(key.split('_')[1])
                                    cantidad = Decimal(value)

                                    if cantidad > 0:
                                        # Bloqueamos la fila para evitar concurrencia
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

                        # Procesar errores o continuar
                        if errores_stock:
                            for error in errores_stock:
                                messages.error(request, f'Stock insuficiente - {error}')
                        elif not detalles_validos:
                            messages.error(request, 'Debe ingresar al menos una cantidad mayor a 0.')
                        else:
                            # 3. Guardado en base de datos: Todo o nada

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

                                # Buscar minibodega de la ruta de hoy, si no existe, la crea con los datos de la ruta
                                minibodega, created = MiniBodega.objects.get_or_create(
                                    ruta=ruta,
                                    defaults={
                                        'fecha': hoy,
                                        'usuario': ruta.usuario,
                                        'vehiculo': ruta.vehiculo,
                                        'estado': True
                                    }
                                )

                                if not created:
                                    if (
                                        minibodega.usuario != ruta.usuario
                                        or minibodega.vehiculo != ruta.vehiculo
                                    ):
                                        minibodega.usuario = ruta.usuario
                                        minibodega.vehiculo = ruta.vehiculo
                                        minibodega.save()

                            # B. Registrar los detalles y mover el stock
                            for variacion, cantidad in detalles_validos:
                                DetalleSalidaPTerminado.objects.create(
                                    salida_p_terminado=salida,
                                    producto_variacion=variacion,
                                    cantidad=cantidad,
                                    precio_unitario=variacion.precio
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

                                    mb_detalle.cantidad_actual += cantidad
                                    mb_detalle.cantidad_inicial = mb_detalle.cantidad_actual
                                    mb_detalle.save()

                            messages.success(request, 'Salida registrada y stock actualizado correctamente.')
                            return redirect('registrar_salidaPT')

                except Exception as e:
                    messages.error(request, f'Error crítico al registrar la salida: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = SalidaForm()

    # =========================================================
    # CONSTRUIR MATRIZ DE PRODUCTOS
    # =========================================================
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

    # =========================================================
    # ORDENAR PRODUCTOS
    # =========================================================
    if usar_orden_personalizado:
        orden_dict = {nombre: i for i, nombre in enumerate(orden_productos)}

        productos_matriz.sort(
            key=lambda item: (
                orden_dict.get(item['producto'].nombre.strip().upper(), 9999),
                item['producto'].nombre
            )
        )
    else:
        productos_matriz.sort(
            key=lambda item: item['producto'].nombre
        )

    return render(request, 'ProductoTerminado/salidas/registrar_salida.html', {
        'form': form,
        'presentaciones': presentaciones,
        'productos_matriz': productos_matriz,
        'usar_orden_personalizado': usar_orden_personalizado
    })

##Hacer asicnrono el stock en las salidas
@login_required
@requiere_roles("Producto Terminado")
def obtener_stock_productos_pt(request):
    variaciones = ProductoVariacion.objects.filter(
        producto__estado=True,
        presentacion__estado=True
    ).values("id", "stock", "stock_min")

    return JsonResponse({
        "stocks": {
            str(v["id"]): {
                "stock": float(v["stock"]),
                "stock_min": float(v["stock_min"])
            }
            for v in variaciones
        }
    })


@login_required
@requiere_roles("Producto Terminado")
def registrar_salida_especial(request):

    # =========================================================
    # CONFIGURACIÓN DE PRODUCTOS ESPECIALES
    # =========================================================
    especiales={
            "ML": {
                "nombre": "Mega Lupita",
                "presentaciones": [
                    "250g",
                    "230g",
                    "60g",
                    "50g",
                    "150g",
                    "40g",
                    ]
            },
            "Y": {
                "nombre": "Yeos",
                "presentaciones": [
                    "200g",
                    "180g",
                    "150g",
                    "120g",
                    "60g",
                    "220g",
                    "250g",
                    "100g",
                    "700g",
                    "650g",
                    ]
            },
            "YML": {
                "nombre": "Super la merced",
                "presentaciones": [
                    "20g",
                    "70g",
                    "80g",
                    "60g",
                    "65g",
                    "100g",
                    "50g",
                    "45g",
                    "40g",
                    "200g",
                    "150g",
                    "180g",
                    "220g",
                    "500g",
                    ]
            },
            "YV": {
                "nombre": "Yeos Victoria",
                "presentaciones": [
                    "200g",
                    "180g",
                    "150g",
                    "220g",
                    "60g",
                    "100g",
                    "250g",
                    "700g",
                    "650g",
                    ]
            },
            "JP": {
                "nombre": "Juaquin Perez",
                "presentaciones": [
                    "750g",
                    "250g",
                    "150g",
                    ]
            },
            "N": {
                "nombre": "Norma",
                "presentaciones": [
                    "620g",
                    "600g",
                    ]
            },
    }

    # =========================================================
    # OBTENER EL ESPECIAL SELECCIONADO
    # =========================================================
    # GET -> cuando cambias el dropdown
    # POST -> cuando mandas el formulario de salida
    especial_seleccionado = (
        request.GET.get("especial")
        or request.POST.get("especial")
        or "ML"
    )

    # Protección por si llega algo inválido
    if especial_seleccionado not in especiales:
        especial_seleccionado = "ML"

    especial = especiales[especial_seleccionado]
    nombres_presentaciones = especial["presentaciones"]

    # =========================================================
    # PRODUCTOS DEL ESPECIAL SELECCIONADO
    # =========================================================
    # Ejemplos:
    # ML -> "ML Enchilado"
    # Y  -> "Y Enchilado"
    # JP -> "JP Enchilado"
    # =========================================================
    productos = ProductoTerminado.objects.filter(
        estado=True,
        nombre__startswith=f"{especial_seleccionado} "
    ).order_by("id").prefetch_related(
        "variaciones",
        "variaciones__presentacion"
    )

    # =========================================================
    # PRESENTACIONES DEL ESPECIAL
    # =========================================================
    presentaciones_qs = PresentacionProductoTerminado.objects.filter(
        estado=True,
        nombre__in=nombres_presentaciones
    )

    # Mantener exactamente el orden definido en el diccionario
    presentaciones = list(presentaciones_qs)

    presentaciones.sort(
        key=lambda p: (
            nombres_presentaciones.index(p.nombre)
            if p.nombre in nombres_presentaciones
            else 99
        )
    )

    # =========================================================
    # POST - REGISTRAR SALIDA
    # =========================================================
    if request.method == "POST":

        form = SalidaForm(request.POST)

        if form.is_valid():

            ruta = form.cleaned_data.get("ruta")
            destino = form.cleaned_data.get("destino")
            nota = form.cleaned_data.get("nota", "")

            # =================================================
            # VALIDAR RUTA
            # =================================================
            if destino == "opcion1" and not ruta:

                messages.error(
                    request,
                    'Debes seleccionar una Ruta específica cuando '
                    'el destino es "Ruta".'
                )

            else:

                try:

                    with transaction.atomic():

                        detalles_validos = []
                        errores_stock = []

                        # =================================================
                        # RECORRER LAS CANTIDADES
                        # =================================================
                        for key, value in request.POST.items():

                            if key.startswith("cantidad_"):

                                try:

                                    variacion_id = int(
                                        key.split("_")[1]
                                    )

                                    cantidad = Decimal(value)

                                    if cantidad > 0:

                                        # =================================
                                        # IMPORTANTE:
                                        # Además del ID validamos que:
                                        #
                                        # 1. Sea del especial seleccionado
                                        # 2. Sea de una presentación permitida
                                        #
                                        # Así no pueden mandar manualmente
                                        # un ID de otro producto.
                                        # =================================
                                        variacion = (
                                            ProductoVariacion.objects
                                            .select_for_update()
                                            .get(
                                                id=variacion_id,
                                                producto__estado=True,
                                                producto__nombre__startswith=(
                                                    f"{especial_seleccionado} "
                                                ),
                                                presentacion__estado=True,
                                                presentacion__nombre__in=(
                                                    nombres_presentaciones
                                                )
                                            )
                                        )

                                        # =================================
                                        # VALIDAR STOCK
                                        # =================================
                                        if cantidad > variacion.stock:

                                            errores_stock.append(
                                                f"{variacion.producto.nombre} "
                                                f"({variacion.presentacion}): "
                                                f"Solicitado {cantidad}, "
                                                f"Disponible {variacion.stock}"
                                            )

                                        else:

                                            detalles_validos.append(
                                                (
                                                    variacion,
                                                    cantidad
                                                )
                                            )

                                except (
                                    ValueError,
                                    TypeError,
                                    ProductoVariacion.DoesNotExist
                                ):
                                    continue

                        # =================================================
                        # ERRORES DE STOCK
                        # =================================================
                        if errores_stock:

                            for error in errores_stock:
                                messages.error(
                                    request,
                                    f"Stock insuficiente - {error}"
                                )

                        elif not detalles_validos:

                            messages.error(
                                request,
                                "Debe ingresar al menos una cantidad "
                                "mayor a 0."
                            )

                        else:

                            # =================================================
                            # CREAR SALIDA
                            # =================================================
                            salida = SalidaPTerminado.objects.create(
                                fecha_salida=timezone.now(),
                                usuario=request.user,
                                ruta=(
                                    ruta
                                    if destino == "opcion1"
                                    else None
                                ),
                                destino=destino,
                                nota=nota
                            )

                           # =================================================
                            # MINIBODEGA
                            # =================================================
                            minibodega = None

                            if destino == "opcion1" and ruta:

                                hoy = timezone.localdate()

                                minibodega, created = (
                                    MiniBodega.objects.get_or_create(
                                        ruta=ruta,
                                        defaults={
                                            "fecha": hoy,
                                            "usuario": ruta.usuario,
                                            "vehiculo": ruta.vehiculo,
                                            "estado": True
                                        }
                                    )
                                )

                                # Si ya existe, actualizar usuario/vehículo
                                # en caso de que hayan cambiado en la Ruta.
                                if not created:

                                    if (
                                        minibodega.usuario != ruta.usuario
                                        or minibodega.vehiculo != ruta.vehiculo
                                    ):

                                        minibodega.usuario = ruta.usuario
                                        minibodega.vehiculo = ruta.vehiculo
                                        minibodega.save()

                            # =================================================
                            # REGISTRAR DETALLES
                            # =================================================
                            for variacion, cantidad in detalles_validos:

                                # -----------------------------------------
                                # Detalle de la salida
                                # -----------------------------------------
                                DetalleSalidaPTerminado.objects.create(
                                salida_p_terminado=salida,
                                producto_variacion=variacion,
                                cantidad=cantidad,
                                precio_unitario=variacion.precio
                                )

                                # -----------------------------------------
                                # Descontar stock principal
                                # -----------------------------------------
                                variacion.stock -= cantidad
                                variacion.save()

                                # -----------------------------------------
                                # Si sale a Ruta -> MiniBodega
                                # -----------------------------------------
                                if minibodega:

                                    mb_detalle, created_mb = (
                                        MiniBodegaDetalle.objects.get_or_create(
                                            mini_bodega=minibodega,
                                            producto_variacion=variacion,
                                            defaults={
                                                "cantidad_inicial": Decimal(
                                                    "0.00"
                                                ),
                                                "cantidad_actual": Decimal(
                                                    "0.00"
                                                )
                                            }
                                        )
                                    )
                                    #

                                    # Se acumula con lo que ya tenga
                                    # la MiniBodega.
                                    mb_detalle.cantidad_actual += cantidad
                                    mb_detalle.cantidad_inicial = mb_detalle.cantidad_actual
                                    mb_detalle.save()

                            messages.success(
                                request,
                                "Salida especial registrada y stock "
                                "actualizado correctamente."
                            )

                            # =================================================
                            # REGRESAR AL MISMO ESPECIAL
                            # =================================================
                            url = reverse(
                                "registrar_salida_especialPT"
                            )

                            return redirect(
                                f"{url}?especial={especial_seleccionado}"
                            )

                except Exception as e:

                    messages.error(
                        request,
                        f"Error crítico al registrar la salida: {str(e)}"
                    )

        else:

            messages.error(
                request,
                "Por favor, corrige los errores en el formulario."
            )

    else:

        form = SalidaForm()

    # =========================================================
    # CONSTRUIR MATRIZ DE PRODUCTOS
    # =========================================================
    productos_matriz = []

    for prod in productos:

        # Relacionar presentación -> variación
        vars_dict = {
            var.presentacion.id: var
            for var in prod.variaciones.all()
        }

        if not vars_dict:
            continue

        celdas = []

        for pres in presentaciones:

            variacion = vars_dict.get(pres.id)

            if variacion:

                celdas.append({
                    "existe": True,
                    "variacion_id": variacion.id,
                    "stock": variacion.stock,
                    "stock_min": variacion.stock_min,
                    "nombre_presentacion": str(pres)
                })

            else:

                celdas.append({
                    "existe": False
                })

        productos_matriz.append({
            "producto": prod,
            "celdas": celdas
        })

    # =========================================================
    # TEMPLATE
    # =========================================================
    return render(
        request,
        "ProductoTerminado/salidas/registrar_salida_especial.html",
        {
            "form": form,
            "especiales": especiales,
            "especial": especial,
            "especial_seleccionado": especial_seleccionado,
            "presentaciones": presentaciones,
            "productos_matriz": productos_matriz
        }
    )



##Corecciones posibles
@login_required
@require_POST
@requiere_roles("Producto Terminado")
def corregir_detalle_entrada(request, detalle_id):

    with transaction.atomic():

        detalle = get_object_or_404(
            DetalleEntradaPTerminado.objects
            .select_for_update()
            .select_related(
                "entrada_p_terminado",
                "producto_variacion",
                "producto_variacion__producto",
                "producto_variacion__presentacion"
            ),
            id=detalle_id
        )

        entrada = detalle.entrada_p_terminado

        # =========================================================
        # SOLO SE PUEDEN CORREGIR ENTRADAS DEL DÍA ACTUAL
        # =========================================================

        if entrada.fecha_entrada.date() != timezone.localdate():

            messages.error(
                request,
                "Solo se pueden corregir entradas del día actual."
            )

            return redirect(
                "detalle_entrada",
                entrada_id=entrada.id
            )

        tipo = request.POST.get("tipo_correccion")


        # =========================================================
        # DETERMINAR CATÁLOGO DE LA ENTRADA
        # =========================================================

        prefijos_especiales = [
            "ML ",
            "Y ",
            "YML ",
            "YV ",
            "JP ",
            "N ",
        ]

        prefijo_especial = None

        detalles_entrada = (
            DetalleEntradaPTerminado.objects
            .select_related(
                "producto_variacion__producto",
                "producto_variacion__presentacion"
            )
            .filter(
                entrada_p_terminado=entrada
            )
        )

        for detalle_entrada in detalles_entrada:

            nombre_producto = (
                detalle_entrada
                .producto_variacion
                .producto
                .nombre
            )

            for prefijo in prefijos_especiales:

                if nombre_producto.startswith(prefijo):

                    prefijo_especial = prefijo
                    break

            if prefijo_especial:
                break


        # =========================================================
        # PRESENTACIONES PERMITIDAS
        # =========================================================

        presentaciones_normales = [
            "Minis",
            "Chico",
            "Mediano",
            "Grande",
            "250g",
            "500g",
            "1kg",
            "Grande 150g",
            "Grande 140g",
            "Pieza",
            "Kiosko",
        ]


        presentaciones_especiales = {

            "ML ": [
                "250g",
                "230g",
                "60g",
                "50g",
                "150g",
                "40g",
            ],

            "Y ": [
                "200g",
                "180g",
                "150g",
                "120g",
                "60g",
                "220g",
                "250g",
                "100g",
                "700g",
                "650g",
            ],

            "YML ": [
                "20g",
                "70g",
                "80g",
                "60g",
                "65g",
                "100g",
                "50g",
                "45g",
                "40g",
                "200g",
                "150g",
                "180g",
                "220g",
                "500g",
            ],

            "YV ": [
                "200g",
                "180g",
                "150g",
                "220g",
                "60g",
                "100g",
                "250g",
                "700g",
                "650g",
            ],

            "JP ": [
                "750g",
                "250g",
                "150g",
            ],

            "N ": [
                "620g",
                "600g",
            ],
        }


        # =========================================================
        # PRODUCTO INCORRECTO
        # =========================================================

        if tipo == "producto":

            producto_nuevo_id = request.POST.get(
                "producto_nuevo_id"
            )

            if not producto_nuevo_id:

                messages.error(
                    request,
                    "Debe seleccionar el producto y presentación correctos."
                )

                return redirect(
                    "detalle_entrada",
                    entrada_id=entrada.id
                )


            try:

                producto_nuevo_id = int(
                    producto_nuevo_id
                )

            except (ValueError, TypeError):

                messages.error(
                    request,
                    "La variación seleccionada no es válida."
                )

                return redirect(
                    "detalle_entrada",
                    entrada_id=entrada.id
                )


            # =====================================================
            # OBTENER LA NUEVA VARIACIÓN
            # =====================================================

            producto_nuevo = get_object_or_404(
                ProductoVariacion.objects
                .select_for_update()
                .select_related(
                    "producto",
                    "presentacion"
                ),
                id=producto_nuevo_id,
                producto__estado=True,
                presentacion__estado=True
            )


            # =====================================================
            # NO PUEDE SER LA MISMA VARIACIÓN
            # =====================================================

            if producto_nuevo.id == detalle.producto_variacion_id:

                messages.error(
                    request,
                    "El producto y presentación seleccionados son los mismos actuales."
                )

                return redirect(
                    "detalle_entrada",
                    entrada_id=entrada.id
                )


            # =====================================================
            # VALIDAR QUE PERTENEZCA AL CATÁLOGO DE LA ENTRADA
            # =====================================================

            nombre_producto_nuevo = producto_nuevo.producto.nombre
            nombre_presentacion_nueva = producto_nuevo.presentacion.nombre


            if prefijo_especial:

                # La entrada es especial.
                # Debe pertenecer al mismo especial.

                if not nombre_producto_nuevo.startswith(
                    prefijo_especial
                ):

                    messages.error(
                        request,
                        "El producto seleccionado no pertenece al tipo de entrada."
                    )

                    return redirect(
                        "detalle_entrada",
                        entrada_id=entrada.id
                    )


                presentaciones_permitidas = (
                    presentaciones_especiales[
                        prefijo_especial
                    ]
                )

                if nombre_presentacion_nueva not in (
                    presentaciones_permitidas
                ):

                    messages.error(
                        request,
                        "La presentación seleccionada no pertenece al tipo de entrada."
                    )

                    return redirect(
                        "detalle_entrada",
                        entrada_id=entrada.id
                    )

            else:

                # La entrada es normal.
                # No puede cambiarse a un producto especial.

                for prefijo in prefijos_especiales:

                    if nombre_producto_nuevo.startswith(
                        prefijo
                    ):

                        messages.error(
                            request,
                            "No se puede seleccionar un producto especial en una entrada normal."
                        )

                        return redirect(
                            "detalle_entrada",
                            entrada_id=entrada.id
                        )


                if nombre_presentacion_nueva not in (
                    presentaciones_normales
                ):

                    messages.error(
                        request,
                        "La presentación seleccionada no pertenece al catálogo normal."
                    )

                    return redirect(
                        "detalle_entrada",
                        entrada_id=entrada.id
                    )


            # =====================================================
            # PRODUCTO ANTERIOR
            # =====================================================

            producto_anterior = (
                ProductoVariacion.objects
                .select_for_update()
                .get(
                    id=detalle.producto_variacion_id
                )
            )

            cantidad = detalle.cantidad


            # =====================================================
            # VERIFICAR SI YA EXISTE LA NUEVA VARIACIÓN
            # EN LA MISMA ENTRADA
            # =====================================================

            detalle_existente = (
                DetalleEntradaPTerminado.objects
                .select_for_update()
                .filter(
                    entrada_p_terminado=entrada,
                    producto_variacion=producto_nuevo
                )
                .exclude(
                    id=detalle.id
                )
                .first()
            )


            # =====================================================
            # AJUSTAR STOCK
            # =====================================================

            # Quitamos la cantidad del producto que estaba
            # registrada originalmente.

            producto_anterior.stock -= cantidad

            producto_anterior.save(
                update_fields=["stock"]
            )


            # Agregamos la cantidad al producto correcto.

            producto_nuevo.stock += cantidad

            producto_nuevo.save(
                update_fields=["stock"]
            )


            # =====================================================
            # SI YA EXISTE LA VARIACIÓN, COMBINAR CANTIDADES
            # =====================================================

            if detalle_existente:

                cantidad_anterior_existente = (
                    detalle_existente.cantidad
                )

                detalle_existente.cantidad += cantidad

                detalle_existente.save(
                    update_fields=["cantidad"]
                )

                detalle.delete()

                detalle_corregido = detalle_existente

                cantidad_nueva = (
                    detalle_existente.cantidad
                )

            else:

                # No existe otro detalle con esa variación.
                # Simplemente cambiamos la variación.

                detalle.producto_variacion = producto_nuevo

                detalle.save(
                    update_fields=["producto_variacion"]
                )

                detalle_corregido = detalle

                cantidad_nueva = cantidad


            # =====================================================
            # REGISTRAR CORRECCIÓN
            # =====================================================

            CorreccionPTerminado.objects.create(

                entrada=entrada,

                detalle_entrada=detalle_corregido,

                tipo_correccion="producto",

                producto_anterior=producto_anterior,

                producto_nuevo=producto_nuevo,

                cantidad_anterior=cantidad,

                cantidad_nueva=cantidad_nueva,

                usuario=request.user
            )


            messages.success(
                request,
                "Producto y presentación corregidos correctamente."
            )


        # =========================================================
        # CANTIDAD INCORRECTA
        # =========================================================

        elif tipo == "cantidad":

            cantidad_nueva = request.POST.get(
                "cantidad_nueva"
            )


            try:

                cantidad_nueva = Decimal(
                    cantidad_nueva
                )

                if cantidad_nueva <= 0:
                    raise ValueError

            except (
                TypeError,
                ValueError,
                InvalidOperation
            ):

                messages.error(
                    request,
                    "La cantidad indicada no es válida."
                )

                return redirect(
                    "detalle_entrada",
                    entrada_id=entrada.id
                )


            cantidad_anterior = detalle.cantidad

            diferencia = (
                cantidad_nueva
                - cantidad_anterior
            )


            producto = (
                ProductoVariacion.objects
                .select_for_update()
                .get(
                    id=detalle.producto_variacion_id
                )
            )


            # Ajustamos únicamente la diferencia.

            producto.stock += diferencia

            producto.save(
                update_fields=["stock"]
            )


            detalle.cantidad = cantidad_nueva

            detalle.save(
                update_fields=["cantidad"]
            )


            CorreccionPTerminado.objects.create(

                entrada=entrada,

                detalle_entrada=detalle,

                tipo_correccion="cantidad",

                producto_anterior=producto,

                producto_nuevo=producto,

                cantidad_anterior=cantidad_anterior,

                cantidad_nueva=cantidad_nueva,

                usuario=request.user
            )


            messages.success(
                request,
                "Cantidad corregida correctamente."
            )


        # =========================================================
        # ELIMINAR PRODUCTO
        # =========================================================

        elif tipo == "eliminar":

            producto = (
                ProductoVariacion.objects
                .select_for_update()
                .get(
                    id=detalle.producto_variacion_id
                )
            )


            cantidad_anterior = detalle.cantidad


            # Revertimos completamente
            # la cantidad que había agregado la entrada.

            producto.stock -= cantidad_anterior

            producto.save(
                update_fields=["stock"]
            )


            CorreccionPTerminado.objects.create(

                entrada=entrada,

                detalle_entrada=None,

                tipo_correccion="eliminar",

                producto_anterior=producto,

                producto_nuevo=None,

                cantidad_anterior=cantidad_anterior,

                cantidad_nueva=Decimal("0.00"),

                usuario=request.user
            )


            detalle.delete()


            messages.success(
                request,
                "Producto eliminado de la entrada correctamente."
            )


        # =========================================================
        # TIPO NO VÁLIDO
        # =========================================================

        else:

            messages.error(
                request,
                "Tipo de corrección no válido."
            )


    return redirect(
        "detalle_entrada",
        entrada_id=entrada.id
    )

@login_required
@requiere_roles("Producto Terminado")
@require_POST
def corregir_detalle_salida(request, detalle_id):

    especiales = {
        "ML": {
            "nombre": "Mega Lupita",
            "presentaciones": [
                "250g", "230g", "60g", "50g", "150g", "40g"
            ]
        },
        "Y": {
            "nombre": "Yeos",
            "presentaciones": [
                "200g", "180g", "150g", "120g", "60g",
                "220g", "250g", "100g", "700g", "650g"
            ]
        },
        "YML": {
            "nombre": "Super la merced",
            "presentaciones": [
                "20g", "70g", "80g", "60g", "65g",
                "100g", "50g", "45g", "40g", "200g",
                "150g", "180g", "220g", "500g"
            ]
        },
        "YV": {
            "nombre": "Yeos Victoria",
            "presentaciones": [
                "200g", "180g", "150g", "220g",
                "60g", "100g", "250g", "700g", "650g"
            ]
        },
        "JP": {
            "nombre": "Juaquin Perez",
            "presentaciones": [
                "750g", "250g", "150g"
            ]
        },
        "N": {
            "nombre": "Norma",
            "presentaciones": [
                "620g", "600g"
            ]
        },
    }

    presentaciones_normales = [
        "Minis",
        "Chico",
        "Mediano",
        "Grande",
        "250g",
        "500g",
        "1kg",
        "Grande 150g",
        "Grande 140g",
        "Pieza",
        "Kiosko",
    ]

    try:

        with transaction.atomic():

            # =====================================================
            # OBTENER DETALLE
            # =====================================================

            detalle = (
                DetalleSalidaPTerminado.objects
                .select_for_update()
                .select_related(
                    "producto_variacion",
                    "producto_variacion__producto",
                    "producto_variacion__presentacion",
                )
                .get(id=detalle_id)
            )

            # =====================================================
            # OBTENER SALIDA
            # =====================================================

            salida = (
                SalidaPTerminado.objects
                .select_for_update()
                .get(id=detalle.salida_p_terminado_id)
            )

            # =====================================================
            # SOLO SE PUEDEN CORREGIR SALIDAS DE HOY
            # =====================================================

            if timezone.localtime(salida.fecha_salida).date() != timezone.localdate():

                messages.error(
                    request,
                    "Solo se pueden corregir salidas del día actual."
                )

                return redirect(
                    "detalle_salida",
                    salida_id=salida.id
                )

            # =====================================================
            # DATOS ORIGINALES
            # =====================================================

            tipo_correccion = request.POST.get("tipo_correccion")

            variacion_anterior_id = detalle.producto_variacion_id
            cantidad_anterior = detalle.cantidad

            # =====================================================
            # DETERMINAR SI ES UNA SALIDA A RUTA
            # =====================================================

            es_ruta = salida.destino == "opcion1"

            minibodega = None

            if es_ruta:

                if not salida.ruta_id:

                    messages.error(
                        request,
                        "La salida está marcada como Ruta, pero no tiene una ruta asignada."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                try:

                    minibodega = (
                        MiniBodega.objects
                        .select_for_update()
                        .get(ruta_id=salida.ruta_id)
                    )

                except MiniBodega.DoesNotExist:

                    messages.error(
                        request,
                        "No se encontró la MiniBodega correspondiente a esta ruta."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

            # =====================================================
            # CORRECCIÓN DE PRODUCTO
            # =====================================================

            if tipo_correccion == "producto":

                producto_nuevo_id = request.POST.get(
                    "producto_nuevo_id"
                )

                if not producto_nuevo_id:

                    messages.error(
                        request,
                        "Debes seleccionar el nuevo producto."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                try:

                    producto_nuevo_id = int(producto_nuevo_id)

                except (TypeError, ValueError):

                    messages.error(
                        request,
                        "El producto seleccionado no es válido."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                # =================================================
                # OBTENER VARIACIÓN NUEVA
                # =================================================

                try:

                    variacion_nueva = (
                        ProductoVariacion.objects
                        .select_for_update()
                        .select_related(
                            "producto",
                            "presentacion"
                        )
                        .get(
                            id=producto_nuevo_id,
                            producto__estado=True,
                            presentacion__estado=True
                        )
                    )

                except ProductoVariacion.DoesNotExist:

                    messages.error(
                        request,
                        "El producto seleccionado no existe o está inactivo."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                # =================================================
                # OBTENER VARIACIÓN ANTERIOR BLOQUEADA
                # =================================================

                variacion_anterior = (
                    ProductoVariacion.objects
                    .select_for_update()
                    .select_related(
                        "producto",
                        "presentacion"
                    )
                    .get(id=variacion_anterior_id)
                )

                # =================================================
                # VALIDAR MISMO CATÁLOGO
                # =================================================

                nombre_anterior = (
                    variacion_anterior.producto.nombre
                )

                nombre_nuevo = (
                    variacion_nueva.producto.nombre
                )

                prefijo_anterior = None
                prefijo_nuevo = None

                for prefijo in especiales.keys():

                    if nombre_anterior.startswith(prefijo + " "):
                        prefijo_anterior = prefijo

                    if nombre_nuevo.startswith(prefijo + " "):
                        prefijo_nuevo = prefijo

                if prefijo_anterior != prefijo_nuevo:

                    messages.error(
                        request,
                        "No puedes cambiar un producto por otro de un catálogo diferente."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                # =================================================
                # VALIDAR PRESENTACIÓN
                # =================================================

                presentacion_nueva = (
                    variacion_nueva.presentacion.nombre
                )

                if prefijo_nuevo:

                    presentaciones_permitidas = especiales[
                        prefijo_nuevo
                    ]["presentaciones"]

                else:

                    presentaciones_permitidas = presentaciones_normales

                if presentacion_nueva not in presentaciones_permitidas:

                    messages.error(
                        request,
                        "La presentación seleccionada no pertenece a este catálogo."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                # =================================================
                # MISMO PRODUCTO
                # =================================================

                if variacion_anterior.id == variacion_nueva.id:

                    messages.warning(
                        request,
                        "El producto seleccionado es el mismo que ya tenía."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                # =================================================
                # VALIDAR STOCK DEL PRODUCTO NUEVO
                # =================================================

                if variacion_nueva.stock < cantidad_anterior:

                    messages.error(
                        request,
                        "No hay suficiente stock del nuevo producto para realizar la corrección."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                # =================================================
                # BUSCAR SI YA EXISTE EN LA MISMA SALIDA
                # =================================================

                detalle_existente = (
                    DetalleSalidaPTerminado.objects
                    .select_for_update()
                    .filter(
                        salida_p_terminado=salida,
                        producto_variacion=variacion_nueva
                    )
                    .exclude(id=detalle.id)
                    .first()
                )

                # =================================================
                # STOCK PRINCIPAL
                # =================================================

                variacion_anterior.stock += cantidad_anterior

                variacion_anterior.save(
                    update_fields=["stock"]
                )

                variacion_nueva.stock -= cantidad_anterior

                variacion_nueva.save(
                    update_fields=["stock"]
                )

                # =================================================
                # MINIBODEGA
                # =================================================

                if minibodega:

                    detalle_mb_anterior = (
                        MiniBodegaDetalle.objects
                        .select_for_update()
                        .filter(
                            mini_bodega=minibodega,
                            producto_variacion=variacion_anterior
                        )
                        .first()
                    )

                    if not detalle_mb_anterior:

                        messages.error(
                            request,
                            "No se encontró el producto anterior en la MiniBodega."
                        )

                        raise ValueError(
                            "Detalle de MiniBodega no encontrado."
                        )

                    if (
                        detalle_mb_anterior.cantidad_actual
                        < cantidad_anterior
                    ):

                        messages.error(
                            request,
                            "No se puede corregir porque la cantidad disponible en la MiniBodega es menor."
                        )

                        raise ValueError(
                            "Cantidad insuficiente en MiniBodega."
                        )

                    # ---------------------------------------------
                    # QUITAR DEL PRODUCTO ANTERIOR
                    # ---------------------------------------------

                    detalle_mb_anterior.cantidad_actual -= (
                        cantidad_anterior
                    )

                    detalle_mb_anterior.cantidad_inicial = (
                        detalle_mb_anterior.cantidad_actual
                    )

                    if detalle_mb_anterior.cantidad_actual == 0:

                        detalle_mb_anterior.delete()

                    else:

                        detalle_mb_anterior.save(
                            update_fields=[
                                "cantidad_actual",
                                "cantidad_inicial"
                            ]
                        )

                    # ---------------------------------------------
                    # AGREGAR AL PRODUCTO NUEVO
                    # ---------------------------------------------

                    detalle_mb_nuevo, creado = (
                        MiniBodegaDetalle.objects
                        .select_for_update()
                        .get_or_create(
                            mini_bodega=minibodega,
                            producto_variacion=variacion_nueva,
                            defaults={
                                "cantidad_inicial": Decimal("0"),
                                "cantidad_actual": Decimal("0"),
                            }
                        )
                    )

                    detalle_mb_nuevo.cantidad_actual += (
                        cantidad_anterior
                    )

                    detalle_mb_nuevo.cantidad_inicial = (
                        detalle_mb_nuevo.cantidad_actual
                    )

                    detalle_mb_nuevo.save(
                        update_fields=[
                            "cantidad_actual",
                            "cantidad_inicial"
                        ]
                    )

                # =================================================
                # REGISTRAR CORRECCIÓN
                # =================================================

                if detalle_existente:

                    detalle_existente.cantidad += cantidad_anterior

                    detalle_existente.precio_unitario = (
                        variacion_nueva.precio
                    )

                    detalle_existente.save(
                        update_fields=[
                            "cantidad",
                            "precio_unitario"
                        ]
                    )

                    CorreccionPTerminado.objects.create(
                        salida=salida,
                        detalle_salida=detalle_existente,
                        tipo_correccion="producto",
                        producto_anterior=variacion_anterior,
                        producto_nuevo=variacion_nueva,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=cantidad_anterior,
                        usuario=request.user,
                    )

                    detalle.delete()

                else:

                    detalle.producto_variacion = variacion_nueva
                    detalle.precio_unitario = variacion_nueva.precio

                    detalle.save(
                        update_fields=[
                            "producto_variacion",
                            "precio_unitario"
                        ]
                    )

                    CorreccionPTerminado.objects.create(
                        salida=salida,
                        detalle_salida=detalle,
                        tipo_correccion="producto",
                        producto_anterior=variacion_anterior,
                        producto_nuevo=variacion_nueva,
                        cantidad_anterior=cantidad_anterior,
                        cantidad_nueva=cantidad_anterior,
                        usuario=request.user,
                    )

                messages.success(
                    request,
                    "Producto corregido correctamente."
                )

            # =====================================================
            # CORRECCIÓN DE CANTIDAD
            # =====================================================

            elif tipo_correccion == "cantidad":

                cantidad_nueva_raw = request.POST.get(
                    "cantidad_nueva"
                )

                try:

                    cantidad_nueva = Decimal(
                        cantidad_nueva_raw
                    )

                except (TypeError, ValueError, InvalidOperation):

                    messages.error(
                        request,
                        "La cantidad indicada no es válida."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                if cantidad_nueva <= 0:

                    messages.error(
                        request,
                        "La cantidad debe ser mayor que cero."
                    )

                    return redirect(
                        "detalle_salida",
                        salida_id=salida.id
                    )

                diferencia = (
                    cantidad_nueva - cantidad_anterior
                )

                variacion_bloqueada = (
                    ProductoVariacion.objects
                    .select_for_update()
                    .get(id=variacion_anterior_id)
                )

                # =================================================
                # AUMENTAR CANTIDAD
                # =================================================

                if diferencia > 0:

                    if variacion_bloqueada.stock < diferencia:

                        messages.error(
                            request,
                            "No hay suficiente stock para aumentar la cantidad de la salida."
                        )

                        return redirect(
                            "detalle_salida",
                            salida_id=salida.id
                        )

                    # Stock principal disminuye
                    variacion_bloqueada.stock -= diferencia

                    variacion_bloqueada.save(
                        update_fields=["stock"]
                    )

                    # MiniBodega aumenta
                    if minibodega:

                        detalle_mb = (
                            MiniBodegaDetalle.objects
                            .select_for_update()
                            .filter(
                                mini_bodega=minibodega,
                                producto_variacion=variacion_bloqueada
                            )
                            .first()
                        )

                        if not detalle_mb:

                            messages.error(
                                request,
                                "No se encontró el producto en la MiniBodega."
                            )

                            raise ValueError(
                                "Detalle de MiniBodega no encontrado."
                            )

                        detalle_mb.cantidad_actual += diferencia

                        detalle_mb.cantidad_inicial = (
                            detalle_mb.cantidad_actual
                        )

                        detalle_mb.save(
                            update_fields=[
                                "cantidad_actual",
                                "cantidad_inicial"
                            ]
                        )

                # =================================================
                # DISMINUIR CANTIDAD
                # =================================================

                elif diferencia < 0:

                    diferencia_reduccion = abs(diferencia)

                    # MiniBodega disminuye
                    if minibodega:

                        detalle_mb = (
                            MiniBodegaDetalle.objects
                            .select_for_update()
                            .filter(
                                mini_bodega=minibodega,
                                producto_variacion=variacion_bloqueada
                            )
                            .first()
                        )

                        if not detalle_mb:

                            messages.error(
                                request,
                                "No se encontró el producto en la MiniBodega."
                            )

                            raise ValueError(
                                "Detalle de MiniBodega no encontrado."
                            )

                        if (
                            detalle_mb.cantidad_actual
                            < diferencia_reduccion
                        ):

                            messages.error(
                                request,
                                "No se puede reducir la salida porque la cantidad disponible en la MiniBodega es menor."
                            )

                            raise ValueError(
                                "Cantidad insuficiente en MiniBodega."
                            )

                        detalle_mb.cantidad_actual -= (
                            diferencia_reduccion
                        )

                        detalle_mb.cantidad_inicial = (
                            detalle_mb.cantidad_actual
                        )

                        if detalle_mb.cantidad_actual == 0:

                            detalle_mb.delete()

                        else:

                            detalle_mb.save(
                                update_fields=[
                                    "cantidad_actual",
                                    "cantidad_inicial"
                                ]
                            )

                    # Stock principal aumenta
                    variacion_bloqueada.stock += (
                        diferencia_reduccion
                    )

                    variacion_bloqueada.save(
                        update_fields=["stock"]
                    )

                # =================================================
                # GUARDAR NUEVA CANTIDAD
                # =================================================

                detalle.cantidad = cantidad_nueva

                detalle.save(
                    update_fields=["cantidad"]
                )

                # =================================================
                # REGISTRAR CORRECCIÓN
                # =================================================

                CorreccionPTerminado.objects.create(
                    salida=salida,
                    detalle_salida=detalle,
                    tipo_correccion="cantidad",
                    producto_anterior=variacion_bloqueada,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=cantidad_nueva,
                    usuario=request.user,
                )

                messages.success(
                    request,
                    "Cantidad corregida correctamente."
                )

            # =====================================================
            # ELIMINAR PRODUCTO
            # =====================================================

            elif tipo_correccion == "eliminar":

                variacion_bloqueada = (
                    ProductoVariacion.objects
                    .select_for_update()
                    .get(id=variacion_anterior_id)
                )

                # =================================================
                # DEVOLVER AL STOCK PRINCIPAL
                # =================================================

                variacion_bloqueada.stock += cantidad_anterior

                variacion_bloqueada.save(
                    update_fields=["stock"]
                )

                # =================================================
                # MINIBODEGA
                # =================================================

                if minibodega:

                    detalle_mb = (
                        MiniBodegaDetalle.objects
                        .select_for_update()
                        .filter(
                            mini_bodega=minibodega,
                            producto_variacion=variacion_bloqueada
                        )
                        .first()
                    )

                    if not detalle_mb:

                        messages.error(
                            request,
                            "No se encontró el producto en la MiniBodega."
                        )

                        raise ValueError(
                            "Detalle de MiniBodega no encontrado."
                        )

                    if (
                        detalle_mb.cantidad_actual
                        < cantidad_anterior
                    ):

                        messages.error(
                            request,
                            "No se puede eliminar porque la cantidad disponible en la MiniBodega es menor."
                        )

                        raise ValueError(
                            "Cantidad insuficiente en MiniBodega."
                        )

                    detalle_mb.cantidad_actual -= cantidad_anterior

                    detalle_mb.cantidad_inicial = (
                        detalle_mb.cantidad_actual
                    )

                    if detalle_mb.cantidad_actual == 0:

                        detalle_mb.delete()

                    else:

                        detalle_mb.save(
                            update_fields=[
                                "cantidad_actual",
                                "cantidad_inicial"
                            ]
                        )

                # =================================================
                # REGISTRAR CORRECCIÓN
                # =================================================

                CorreccionPTerminado.objects.create(
                    salida=salida,
                    detalle_salida=detalle,
                    tipo_correccion="eliminar",
                    producto_anterior=variacion_bloqueada,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=Decimal("0.00"),
                    usuario=request.user,
                )

                # =================================================
                # ELIMINAR DETALLE DE LA SALIDA
                # =================================================

                detalle.delete()

                messages.success(
                    request,
                    "Producto eliminado correctamente."
                )

            else:

                messages.error(
                    request,
                    "Tipo de corrección no válido."
                )

    except ValueError:
        pass

    return redirect(
        "detalle_salida",
        salida_id=salida.id
    )


# View de Presentacio de productos terminados----------------------------------------#

from django.shortcuts import render, redirect, get_object_or_404
from .models import PresentacionProductoTerminado
from .forms import PresentacionProductoTerminadoForm

@login_required
@requiere_roles("Recursos Humanos")
def lista_presentaciones(request):
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        presentaciones = PresentacionProductoTerminado.objects.all()
    else:
        presentaciones = PresentacionProductoTerminado.objects.filter(estado=True)

    return render(request, 'ProductoTerminado/presentaciones/lista.html',
                  {'presentaciones': presentaciones, 'mostrar_todos': mostrar_todos})


@login_required
@requiere_roles("Recursos Humanos")
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

@login_required
@requiere_roles("Recursos Humanos")
def editar_presentacion(request, pk):
    presentacion = get_object_or_404(PresentacionProductoTerminado, pk=pk)
    form = PresentacionProductoTerminadoForm(request.POST or None, request.FILES or None, instance=presentacion)
    if form.is_valid():
        form.save()
        messages.success(request, "Presentación actualizada correctamente.")
        return redirect('lista_presentaciones')
    return render(request, 'ProductoTerminado/presentaciones/editar.html', {'form': form, 'presentacion': presentacion})

@login_required
@requiere_roles("Recursos Humanos")
def eliminar_presentacion(request, pk):
    presentacion = get_object_or_404(PresentacionProductoTerminado, pk=pk)
    presentacion.estado = False
    presentacion.save()
    messages.success(request, "Presentación desactivada correctamente.")
    return redirect('lista_presentaciones')


@login_required
@requiere_roles("Producto Terminado", "Recursos Humanos")
def historial_entradas(request):

    hoy = timezone.localdate()

    desde = request.GET.get("desde") or hoy.strftime("%Y-%m-%d")
    hasta = request.GET.get("hasta") or hoy.strftime("%Y-%m-%d")

    entradas = (
    EntradaPTerminado.objects
    .select_related("usuario")
    .annotate(
        fue_corregida=Exists(
            CorreccionPTerminado.objects.filter(
                entrada=OuterRef("pk")
            )
        )
    )
    .filter(
        fecha_entrada__date__gte=desde,
        fecha_entrada__date__lte=hasta
    )
    .order_by("-fecha_entrada"))

    return render(
        request,
        "ProductoTerminado/entradas/historial_entradas.html",
        {
            "entradas": entradas,
            "desde": desde,
            "hasta": hasta,
        }
    )

@login_required
@requiere_roles("Producto Terminado", "Recursos Humanos")
def detalle_entrada(request, entrada_id):

    entrada = get_object_or_404(
        EntradaPTerminado.objects.select_related("usuario"),
        id=entrada_id
    )

    detalles = (
        DetalleEntradaPTerminado.objects
        .filter(entrada_p_terminado=entrada)
        .select_related(
            "producto_variacion",
            "producto_variacion__producto",
            "producto_variacion__presentacion"
        )
        .order_by("id")
    )

    es_hoy = (
        timezone.localtime(entrada.fecha_entrada).date() == timezone.localdate()
    )

    # =========================================================
    # DETERMINAR CATÁLOGO DE LA ENTRADA
    # =========================================================

    prefijos_especiales = [
        "ML ",
        "Y ",
        "YML ",
        "YV ",
        "JP ",
        "N ",
    ]

    prefijo_especial = None

    for detalle in detalles:
        nombre_producto = detalle.producto_variacion.producto.nombre

        for prefijo in prefijos_especiales:
            if nombre_producto.startswith(prefijo):
                prefijo_especial = prefijo
                break

        if prefijo_especial:
            break

    # =========================================================
    # OBTENER VARIACIONES PERMITIDAS
    # =========================================================

    if prefijo_especial:

        # Entrada especial
        variaciones = (
            ProductoVariacion.objects
            .filter(
                producto__estado=True,
                producto__nombre__startswith=prefijo_especial,
                presentacion__estado=True
            )
            .select_related(
                "producto",
                "presentacion"
            )
            .order_by(
                "producto__nombre",
                "presentacion__nombre"
            )
        )

    else:

        # Entrada normal
        variaciones = (
            ProductoVariacion.objects
            .filter(
                producto__estado=True,
                presentacion__estado=True
            )
            .exclude(
                Q(producto__nombre__startswith="ML ") |
                Q(producto__nombre__startswith="Y ") |
                Q(producto__nombre__startswith="YML ") |
                Q(producto__nombre__startswith="YV ") |
                Q(producto__nombre__startswith="JP ") |
                Q(producto__nombre__startswith="N ")
            )
            .select_related(
                "producto",
                "presentacion"
            )
            .order_by(
                "producto__nombre",
                "presentacion__nombre"
            )
        )

    # =========================================================
    # HISTORIAL DE CORRECCIONES
    # =========================================================

    correcciones = (
        entrada.correcciones
        .select_related(
            "producto_anterior__producto",
            "producto_anterior__presentacion",
            "producto_nuevo__producto",
            "producto_nuevo__presentacion",
            "usuario"
        )
        .order_by("fecha_correccion", "id")
    )

    return render(
        request,
        "ProductoTerminado/entradas/detalle_entrada.html",
        {
            "entrada": entrada,
            "detalles": detalles,
            "es_hoy": es_hoy,
            "variaciones": variaciones,
            "correcciones": correcciones,
        }
    )



@login_required
@requiere_roles("Producto Terminado", "Recursos Humanos")
def historial_salidas(request):
    hoy=timezone.localdate()

    desde=request.GET.get("desde") or hoy.strftime("%Y-%m-%d")
    hasta=request.GET.get("hasta") or hoy.strftime("%Y-%m-%d")

    salidas = (
        SalidaPTerminado.objects
        .select_related("usuario", "ruta")
        .annotate(
            fue_corregida=Exists(
                CorreccionPTerminado.objects.filter(
                    salida=OuterRef("pk")
                )
            )
        )
        .filter(
            fecha_salida__date__gte=desde,
            fecha_salida__date__lte=hasta
        )
        .order_by("-fecha_salida")
    )

    return render(
        request,
        "ProductoTerminado/salidas/historial_salidas.html",
        {
            "salidas": salidas,
            "desde": desde,
            "hasta": hasta,
        }
    )

@login_required
@requiere_roles("Producto Terminado", "Recursos Humanos")
def detalle_salida(request, salida_id):

    salida = get_object_or_404(
        SalidaPTerminado.objects.select_related("usuario", "ruta"),
        id=salida_id
    )

    # =========================================================
    # EDITAR NOTA DE LA SALIDA
    # =========================================================
    if request.method == "POST" and request.POST.get("accion") == "editar_nota":

        if not request.user.is_superuser and (
            not request.user.rol or
            request.user.rol.nombre not in ["Administrador", "Producto Terminado"]
        ):
            return HttpResponseForbidden("No tienes permiso para editar la nota.")

        nueva_nota = request.POST.get("nota", "").strip()

        salida.nota = nueva_nota
        salida.save(update_fields=["nota"])

        messages.success(request, "La nota se actualizó correctamente.")

        return redirect("detalle_salida", salida_id=salida.id)

    detalles = (
        DetalleSalidaPTerminado.objects
        .filter(salida_p_terminado=salida)
        .select_related(
            "producto_variacion",
            "producto_variacion__producto",
            "producto_variacion__presentacion"
        )
        .order_by("id")
    )

    total_salida = sum(
        (
            detalle.subtotal
            for detalle in detalles
            if detalle.subtotal is not None
        ),
        Decimal("0.00")
    )

    # =========================================================
    # SABER SI LA SALIDA ES DE HOY
    # =========================================================

    es_hoy = (
        timezone.localtime(salida.fecha_salida).date()
        == timezone.localdate()
    )

    # =========================================================
    # DETERMINAR CATÁLOGO DE LA SALIDA
    # =========================================================

    prefijos_especiales = [
        "ML ",
        "Y ",
        "YML ",
        "YV ",
        "JP ",
        "N ",
    ]

    prefijo_especial = None

    for detalle in detalles:
        nombre_producto = detalle.producto_variacion.producto.nombre

        for prefijo in prefijos_especiales:
            if nombre_producto.startswith(prefijo):
                prefijo_especial = prefijo
                break

        if prefijo_especial:
            break

    # =========================================================
    # OBTENER VARIACIONES PERMITIDAS
    # =========================================================

    if prefijo_especial:

        variaciones = (
            ProductoVariacion.objects
            .filter(
                producto__estado=True,
                producto__nombre__startswith=prefijo_especial,
                presentacion__estado=True
            )
            .select_related(
                "producto",
                "presentacion"
            )
            .order_by(
                "producto__nombre",
                "presentacion__nombre"
            )
        )

    else:

        variaciones = (
            ProductoVariacion.objects
            .filter(
                producto__estado=True,
                presentacion__estado=True
            )
            .exclude(
                Q(producto__nombre__startswith="ML ") |
                Q(producto__nombre__startswith="Y ") |
                Q(producto__nombre__startswith="YML ") |
                Q(producto__nombre__startswith="YV ") |
                Q(producto__nombre__startswith="JP ") |
                Q(producto__nombre__startswith="N ")
            )
            .select_related(
                "producto",
                "presentacion"
            )
            .order_by(
                "producto__nombre",
                "presentacion__nombre"
            )
        )

    # =========================================================
    # HISTORIAL DE CORRECCIONES
    # =========================================================

    correcciones = (
        salida.correcciones
        .select_related(
            "producto_anterior__producto",
            "producto_anterior__presentacion",
            "producto_nuevo__producto",
            "producto_nuevo__presentacion",
            "usuario"
        )
        .order_by("fecha_correccion", "id")
    )

    return render(
        request,
        "ProductoTerminado/salidas/detalle_salida.html",
        {
            "salida": salida,
            "detalles": detalles,
            "total_salida": total_salida,
            "es_hoy": es_hoy,
            "variaciones": variaciones,
            "correcciones": correcciones,
        }
    )


@login_required
@requiere_roles("Producto Terminado","Producción")
def lista_productos_terminados(request):
    variaciones=ProductoVariacion.objects.filter(
        producto__estado=True

    ).select_related(
        'producto',
        'producto__categoria_producto',
        'presentacion'
    ).order_by(
        'producto__nombre',
        'presentacion__nombre'
    )


    return render(
        request,
        'Produccion/lista_produccion_productoT.html',
        {'variaciones':variaciones}
    )




@login_required
@requiere_roles("Producto Terminado")
def realizar_corte_pt(request):
    variaciones = list(
        ProductoVariacion.objects.filter(
            producto__estado=True
        ).select_related('producto', 'presentacion')
    )

    # Orden personalizado de productos y presentaciones
    orden_productos = {
        nombre.upper(): i
        for i, nombre in enumerate(ORDEN_PRODUCTOS_REPORTE_DIARIO_PT)
    }
    orden_presentaciones = {
        nombre.upper(): i
        for i, nombre in enumerate(ORDEN_PRESENTACIONES_REPORTE_DIARIO_PT)
    }
    prefijos_especiales = ("ML ", "Y ", "YML ", "YV ", "JP ", "N ")

    def clave_orden_corte(variacion):
        producto = variacion.producto.nombre.strip().upper()
        presentacion = variacion.presentacion.nombre.strip().upper()
        es_especial = producto.startswith(prefijos_especiales)

        return (
            1 if es_especial else 0,
            orden_productos.get(producto, len(orden_productos)),
            producto if producto not in orden_productos else '',
            orden_presentaciones.get(presentacion, len(orden_presentaciones)),
            presentacion
        )

    variaciones.sort(key=clave_orden_corte)

    if request.method == "POST":
        form = CorteInventarioPTerminadoForm(request.POST)

        if form.is_valid():
            # Validar el stock real de todos los productos
            stocks_reales = {}

            for variacion in variaciones:
                stock_real_str = request.POST.get(f'stock_real_{variacion.id}')

                if stock_real_str is None or stock_real_str == '':
                    messages.error(
                        request,
                        f"No se recibió el stock real de "
                        f"{variacion.producto.nombre} - "
                        f"{variacion.presentacion.nombre}."
                    )
                    return render(request, 'ProductoTerminado/cortes/realizar_corte.html', {
                        'form': form,
                        'variaciones': variaciones,
                    })

                try:
                    stock_real = Decimal(stock_real_str)
                except (InvalidOperation, ValueError):
                    messages.error(
                        request,
                        f"El stock real de "
                        f"{variacion.producto.nombre} - "
                        f"{variacion.presentacion.nombre} no es válido."
                    )
                    return render(request, 'ProductoTerminado/cortes/realizar_corte.html', {
                        'form': form,
                        'variaciones': variaciones,
                    })

                if stock_real < Decimal('0'):
                    messages.error(
                        request,
                        f"El stock real de "
                        f"{variacion.producto.nombre} - "
                        f"{variacion.presentacion.nombre} no puede ser negativo."
                    )
                    return render(request, 'ProductoTerminado/cortes/realizar_corte.html', {
                        'form': form,
                        'variaciones': variaciones,
                    })

                stocks_reales[variacion.id] = stock_real

            # Crear el corte únicamente cuando todos los valores sean válidos
            with transaction.atomic():
                corte = form.save(commit=False)
                corte.usuario = request.user
                corte.fecha = timezone.now()
                corte.estado = 'correcto'
                corte.save()

                requiere_ajuste = False

                for variacion in variaciones:
                    stock_teorico = variacion.stock
                    stock_real = stocks_reales[variacion.id]
                    diferencia = stock_real - stock_teorico
                    ajuste_necesario = diferencia != Decimal('0')

                    if ajuste_necesario:
                        requiere_ajuste = True

                    DetalleCorteInventarioPTerminado.objects.create(
                        corte_inventario=corte,
                        producto_variacion=variacion,
                        stock_teorico=stock_teorico,
                        stock_real=stock_real,
                        diferencia=diferencia,
                        ajuste_necesario=ajuste_necesario
                    )

                if requiere_ajuste:
                    corte.estado = 'pendiente'
                    corte.save()

            messages.success(request, "Corte de inventario registrado correctamente.")
            return redirect('lista_cortes_pt')

        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = CorteInventarioPTerminadoForm()

    context = {
        'form': form,
        'variaciones': variaciones,
    }
    return render(request, 'ProductoTerminado/cortes/realizar_corte.html', context)





@login_required
@requiere_roles("Producto Terminado")
def lista_cortes_pt(request):

    cortes = CorteInventarioPTerminado.objects.all().select_related(
        'usuario'
    ).order_by('-fecha')

    return render(
        request,
        'ProductoTerminado/cortes/lista_cortes.html',
        {'cortes': cortes}
    )



@login_required
@requiere_roles("Producto Terminado")
def ajustar_inventario_pt(request, corte_id):
    corte = get_object_or_404(CorteInventarioPTerminado, id=corte_id)

    detalles = ordenar_detalles_corte_pt(
        corte.detallecorteinventariopterminado_set.all().select_related(
            'producto_variacion__producto',
            'producto_variacion__presentacion'
        )
    )

    if request.method == "POST":
        for detalle in detalles:
            if detalle.diferencia != Decimal('0'):
                variacion = detalle.producto_variacion
                variacion.stock = detalle.stock_real
                variacion.save()

        corte.estado = 'ajustado'
        corte.save()

        messages.success(request, "Ajuste realizado correctamente.")
        return redirect('lista_cortes_pt')

    context = {
        'corte': corte,
        'detalles': detalles,
    }
    return render(request, 'ProductoTerminado/cortes/ajuste_inventario.html', context)





@login_required
@requiere_roles("Producto Terminado")
def detalle_corte_pt(request, corte_id):
    corte = get_object_or_404(CorteInventarioPTerminado, id=corte_id)

    detalles = ordenar_detalles_corte_pt(
        corte.detallecorteinventariopterminado_set.all().select_related(
            'producto_variacion__producto',
            'producto_variacion__presentacion'
        )
    )

    context = {
        'corte': corte,
        'detalles': detalles,
    }
    return render(request, 'ProductoTerminado/cortes/detalle_corte.html', context)




def ordenar_detalles_corte_pt(detalles):
    orden_productos = {nombre.upper(): i for i, nombre in enumerate(ORDEN_PRODUCTOS_REPORTE_DIARIO_PT)}
    orden_presentaciones = {nombre.upper(): i for i, nombre in enumerate(ORDEN_PRESENTACIONES_REPORTE_DIARIO_PT)}
    prefijos_especiales = ("ML ", "Y ", "YML ", "YV ", "JP ", "N ")

    def clave(detalle):
        variacion = detalle.producto_variacion
        producto = variacion.producto.nombre.strip().upper()
        presentacion = variacion.presentacion.nombre.strip().upper()
        es_especial = producto.startswith(prefijos_especiales)

        return (
            1 if es_especial else 0,
            orden_productos.get(producto, len(orden_productos)),
            producto if producto not in orden_productos else '',
            orden_presentaciones.get(presentacion, len(orden_presentaciones)),
            presentacion
        )

    return sorted(detalles, key=clave)



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

##Reporte semanal

@login_required
@requiere_roles("Producto Terminado", "Recursos Humanos")
def reporte_salidas_semanales_pt(request):
    destino = request.GET.get('destino', 'todos')
    destinos_validos = {'opcion1', 'opcion2', 'opcion3', 'opcion4'}
    if destino not in destinos_validos: destino = 'todos'

    ruta_param = request.GET.get('ruta', 'todas')
    ruta_id = int(ruta_param) if ruta_param.isdigit() and 1 <= int(ruta_param) <= 11 else None
    semanas = []
    for fecha_str in request.GET.get('semanas', '').split(','):
        try: semanas.append(datetime.strptime(fecha_str, '%Y-%m-%d').date())
        except ValueError: continue

    if not semanas:
        hoy = now().date()
        semanas = [hoy - timedelta(days=(hoy.weekday() - 2) % 7)]

    filtro_semanas = Q()
    for inicio in semanas:
        filtro_semanas |= Q(salida_p_terminado__fecha_salida__date__range=(inicio, inicio + timedelta(days=6))) & ~Q(salida_p_terminado__fecha_salida__date=inicio + timedelta(days=4))

    salidas = DetalleSalidaPTerminado.objects.filter(filtro_semanas, cantidad__gt=0)
    if destino in destinos_validos:
        salidas = salidas.filter(salida_p_terminado__destino=destino)
    if destino == 'opcion1' and ruta_id is not None:
        salidas = salidas.filter(salida_p_terminado__ruta_id=ruta_id)

    orden_productos = [
        "PISTACHE", "ENCHILADO", "JAPONES", "JAPONES FUEGO", "MACHO",
        "HORNEADO", "CASCARITA", "SURTIDO", "HABA PELADA", "HABA CON CASCARA",
        "GARBANZA", "GARAPIÑADO", "GOMITA", "LUNETA", "HUEVITO CHOCOLATE",
        "GALLETA MARINA", "CIRUELA", "PASAS", "SEMILLA DE CALABAZA",
        "SEMILLA DE GIRASOL", "NUEZ", "ALMENDRA", "GRANOLA", "CHILE DE ARBOL",
        "CHILE PULLA", "CHILE CASCABEL", "CAMARON", "CAMARON MOLIDO",
        "CHARAL NATURAL", "CHARAL ADOBADO", "CECINA NATURAL", "CECINA ADOBADA",
        "CECINA DE LIMON", "CECINA CHILTEPIN", "CECINA CHIPOTLE",
        "CECINA HABANERO", "CECINA ARTESANAL", "PAPA FRITA",
        "CHURRO DE MASA", "CHURRO DELGADO", "CHICHARRON", "CHICHARRON CRAC",
        "PLATANO", "TOSTADA", "MIEL", "TIRA DE CC MINI", "TIRA DE DULCE",
        "MIX VERDE", "MIX ROJO"
    ]
    orden_presentaciones = [
        "Minis", "Chico", "Mediano", "Grande", "250g", "500g",
        "1kg", "Kiosko", "Grande 150g", "Grande 140g", "Pieza"
    ]
    prefijos_especiales = ["ML ", "Y ", "YML ", "YV ", "JP ", "N "]
    mapa_productos = {nombre.upper(): i for i, nombre in enumerate(orden_productos)}
    mapa_presentaciones = {nombre.upper(): i for i, nombre in enumerate(orden_presentaciones)}

    productos = salidas.values(
        'producto_variacion_id',
        'producto_variacion__producto__nombre',
        'producto_variacion__presentacion__nombre'
    ).annotate(total_salidas=Sum('cantidad'))

    datos = []
    for item in productos:
        nombre = (item['producto_variacion__producto__nombre'] or '').strip()
        presentacion = (item['producto_variacion__presentacion__nombre'] or '').strip()
        nombre_mayus = nombre.upper()
        grupo = next((prefijo.strip() for prefijo in prefijos_especiales if nombre_mayus.startswith(prefijo)), 'NORMALES')
        datos.append({
            'producto_variacion_id': item['producto_variacion_id'],
            'producto': nombre,
            'presentacion': presentacion,
            'total_salido': float(item['total_salidas']),
            'grupo': grupo
        })

    datos.sort(key=lambda item: (
        mapa_productos.get(item['producto'].upper(), len(orden_productos)),
        item['producto'].upper() if item['producto'].upper() not in mapa_productos else '',
        mapa_presentaciones.get(item['presentacion'].upper(), len(orden_presentaciones)),
        item['presentacion'].upper()
    ))

    return JsonResponse({
        'semanas': [{'inicio': str(fecha), 'fin': str(fecha + timedelta(days=6))} for fecha in semanas],
        'destino': destino,
        'ruta': ruta_param if destino == 'opcion1' else 'todas',
        'productos': datos,
        'orden_presentaciones': orden_presentaciones
    })


@login_required
@requiere_roles("Producto Terminado","Recursos Humanos")
def detalle_salida_semanal_pt(
    request,
    producto_variacion_id
):

    destino = request.GET.get(
        'destino',
        'opcion1'
    )

    destinos_validos = {
        'opcion1',
        'opcion2',
        'opcion3',
        'opcion4',
    }

    if destino not in destinos_validos:
        destino = 'opcion1'


    ruta_param = request.GET.get('ruta', 'todas')
    ruta_id = int(ruta_param) if ruta_param.isdigit() and 1 <= int(ruta_param) <= 11 else None
    semanas_param = request.GET.get(
        'semanas',
        ''
    )

    semanas = []

    if semanas_param:

        for fecha_str in semanas_param.split(','):

            try:

                fecha = datetime.strptime(
                    fecha_str,
                    '%Y-%m-%d'
                ).date()

                semanas.append(fecha)

            except ValueError:
                continue


    # Si no hay semanas, usar la actual

    if not semanas:

        hoy = now().date()

        dias_desde_miercoles = (
            hoy.weekday() - 2
        ) % 7

        inicio_semana = (
            hoy -
            timedelta(days=dias_desde_miercoles)
        )

        semanas = [
            inicio_semana
        ]


    # Construir filtro para todas las semanas

    filtros_semana = []

    for inicio_semana in semanas:

        fin_semana = (
            inicio_semana +
            timedelta(days=6)
        )

        domingo = (
            inicio_semana +
            timedelta(days=4)
        )

        filtros_semana.append(
            Q(
                salida_p_terminado__fecha_salida__date__range=(
                    inicio_semana,
                    fin_semana
                )
            )
            &
            ~Q(
                salida_p_terminado__fecha_salida__date=domingo
            )
        )


    filtro_semanas = filtros_semana[0]

    for filtro in filtros_semana[1:]:

        filtro_semanas |= filtro


    detalles = (
        DetalleSalidaPTerminado.objects
        .filter(
            Q(
                producto_variacion_id=producto_variacion_id
            )
            & filtro_semanas
            & Q(
                salida_p_terminado__destino=destino
            )
            & Q(
                cantidad__gt=0
            )
        )
        .select_related(
            'salida_p_terminado__ruta__usuario'
        )
    )

    if ruta_id is not None:
        detalles = detalles.filter(salida_p_terminado__ruta_id=ruta_id)


    repartidores = {}


    for detalle in detalles:

        salida = detalle.salida_p_terminado

        fecha = salida.fecha_salida.date()

        repartidor = None

        if salida.ruta and salida.ruta.usuario:

            repartidor = salida.ruta.usuario


        if repartidor is None:
            continue


        repartidor_id = repartidor.id


        if repartidor_id not in repartidores:

            repartidores[repartidor_id] = {

                'repartidor_id':
                    repartidor_id,

                'repartidor': (
                    repartidor.get_full_name()
                    or repartidor.username
                ),

                'miercoles': 0,
                'jueves': 0,
                'viernes': 0,
                'sabado': 0,
                'lunes': 0,
                'martes': 0,

                'total': 0,
            }


        cantidad = float(
            detalle.cantidad
        )

        dia_semana = fecha.weekday()


        if dia_semana == 2:

            repartidores[
                repartidor_id
            ]['miercoles'] += cantidad

        elif dia_semana == 3:

            repartidores[
                repartidor_id
            ]['jueves'] += cantidad

        elif dia_semana == 4:

            repartidores[
                repartidor_id
            ]['viernes'] += cantidad

        elif dia_semana == 5:

            repartidores[
                repartidor_id
            ]['sabado'] += cantidad

        elif dia_semana == 0:

            repartidores[
                repartidor_id
            ]['lunes'] += cantidad

        elif dia_semana == 1:

            repartidores[
                repartidor_id
            ]['martes'] += cantidad


        repartidores[
            repartidor_id
        ]['total'] += cantidad


    return JsonResponse({

        'producto_variacion_id':
            producto_variacion_id,

        'semanas': [
            {
                'inicio': str(fecha),
                'fin': str(
                    fecha + timedelta(days=6)
                )
            }
            for fecha in semanas
        ],

        'destino': destino,

        'repartidores':
            list(
                repartidores.values()
            ),
    })



@login_required
@requiere_roles("Producto Terminado","Recursos Humanos")
def resumen_destinos_salida_semanal_pt(request, producto_variacion_id):

    semanas_param = request.GET.get('semanas', '')
    semanas = []

    if semanas_param:
        for fecha_str in semanas_param.split(','):
            try:
                fecha = datetime.strptime(
                    fecha_str, '%Y-%m-%d'
                ).date()
                semanas.append(fecha)
            except ValueError:
                continue

    # Si no hay semanas seleccionadas, usar la actual
    if not semanas:
        hoy = now().date()
        dias_desde_miercoles = (hoy.weekday() - 2) % 7
        inicio_semana = hoy - timedelta(days=dias_desde_miercoles)
        semanas = [inicio_semana]

    # Construir filtros de semanas, excluyendo domingos
    filtros_semana = []

    for inicio_semana in semanas:
        fin_semana = inicio_semana + timedelta(days=6)
        domingo = inicio_semana + timedelta(days=4)

        filtros_semana.append(
            Q(
                salida_p_terminado__fecha_salida__date__range=(
                    inicio_semana,
                    fin_semana
                )
            )
            &
            ~Q(
                salida_p_terminado__fecha_salida__date=domingo
            )
        )

    filtro_semanas = filtros_semana[0]

    for filtro in filtros_semana[1:]:
        filtro_semanas |= filtro

    detalles = (
        DetalleSalidaPTerminado.objects
        .filter(
            Q(producto_variacion_id=producto_variacion_id)
            & filtro_semanas
            & Q(cantidad__gt=0)
        )
        .values(
            'salida_p_terminado__destino',
            'salida_p_terminado__fecha_salida__date'
        )
        .annotate(total=Sum('cantidad'))
    )

    dias = [
        'miercoles',
        'jueves',
        'viernes',
        'sabado',
        'lunes',
        'martes'
    ]

    nombres_destinos = {
        'opcion1': 'Ruta',
        'opcion2': 'Mitsu',
        'opcion3': 'Maestro',
        'opcion4': 'Otros'
    }

    destinos = {}

    for codigo, nombre in nombres_destinos.items():
        destinos[codigo] = {
            'nombre': nombre,
            **{dia: 0 for dia in dias},
            'total': 0
        }

    dias_por_weekday = {
        2: 'miercoles',
        3: 'jueves',
        4: 'viernes',
        5: 'sabado',
        0: 'lunes',
        1: 'martes'
    }

    for item in detalles:

        codigo = item['salida_p_terminado__destino']
        fecha = item['salida_p_terminado__fecha_salida__date']

        if codigo not in destinos or fecha is None:
            continue

        dia = dias_por_weekday.get(fecha.weekday())

        if not dia:
            continue

        cantidad = float(item['total'])

        destinos[codigo][dia] += cantidad
        destinos[codigo]['total'] += cantidad

    totales_dias = {
        dia: sum(destino[dia] for destino in destinos.values())
        for dia in dias
    }

    total_general = sum(
        destino['total'] for destino in destinos.values()
    )

    return JsonResponse({
        'producto_variacion_id': producto_variacion_id,
        'semanas': [
            {
                'inicio': str(fecha),
                'fin': str(fecha + timedelta(days=6))
            }
            for fecha in semanas
        ],
        'destinos': list(destinos.values()),
        'totales_dias': totales_dias,
        'total': total_general
    })




@login_required
@requiere_roles("Producto Terminado","Recursos Humanos")
def semanas_disponibles_salidas_pt(request):

    primer_detalle = (
        DetalleSalidaPTerminado.objects
        .filter(
            cantidad__gt=0
        )
        .order_by(
            'salida_p_terminado__fecha_salida'
        )
        .first()
    )

    if not primer_detalle:

        return JsonResponse({
            'semanas': []
        })


    primera_fecha = (
        primer_detalle
        .salida_p_terminado
        .fecha_salida
        .date()
    )


    hoy = now().date()


    # =========================================================
    # SEMANA OPERATIVA ACTUAL
    # Miércoles -> Martes
    # =========================================================

    dias_desde_miercoles = (
        hoy.weekday() - 2
    ) % 7


    inicio_semana_actual = (
        hoy - timedelta(
            days=dias_desde_miercoles
        )
    )


    # =========================================================
    # PRIMERA SEMANA CONSIDERADA
    # =========================================================

    dias_desde_miercoles = (
        primera_fecha.weekday() - 2
    ) % 7


    fecha_semana = (
        primera_fecha - timedelta(
            days=dias_desde_miercoles
        )
    )


    semanas = []


    # =========================================================
    # RECORRER SEMANAS
    # =========================================================

    while fecha_semana <= inicio_semana_actual:

        fin_semana = (
            fecha_semana + timedelta(
                days=6
            )
        )


        domingo = (
            fecha_semana + timedelta(
                days=4
            )
        )


        tiene_movimientos = (
            DetalleSalidaPTerminado.objects
            .filter(
                salida_p_terminado__fecha_salida__date__range=(
                    fecha_semana,
                    fin_semana
                ),
                cantidad__gt=0
            )
            .exclude(
                salida_p_terminado__fecha_salida__date=domingo
            )
            .exists()
        )


        if tiene_movimientos:

            semanas.append({

                'inicio': str(
                    fecha_semana
                ),

                'fin': str(
                    fin_semana
                ),

                'anio': fecha_semana.year,

            })


        fecha_semana += timedelta(
            days=7
        )


    # Más reciente primero

    semanas.reverse()


    return JsonResponse({

        'semanas': semanas

    })


@login_required
@requiere_roles("Producto Terminado","Recursos Humanos")
def reporte_salidas_semanales_pt_html(request):
    return render(
        request,
        'ProductoTerminado/salidas/reporte_salidas_semanales.html'
    )


@login_required
@requiere_roles("Producto Terminado","Recursos Humanos")
def reporte_salidas_semanales_pt_html(request):
    return render(
        request,
        'ProductoTerminado/salidas/reporte_salidas_semanales.html'
    )

#Reporte diario

@login_required
@requiere_roles("Administrador", "Producto Terminado", "Recursos Humanos")
def reporte_diario_pt_html(request):
    return render(request, "ProductoTerminado/reportes/reporte_diario_pt.html", {
        "fecha_actual": timezone.localdate().isoformat()
    })

ORDEN_PRESENTACIONES_REPORTE_DIARIO_PT = [
    "Minis", "Chico", "Mediano", "Grande", "250g", "500g",
    "1kg", "Kiosko", "Grande 150g", "Grande 140g", "Pieza"
]

ORDEN_PRODUCTOS_REPORTE_DIARIO_PT = [
    "PISTACHE", "ENCHILADO", "JAPONES", "JAPONES FUEGO", "MACHO",
    "HORNEADO", "CASCARITA", "SURTIDO", "HABA PELADA", "HABA CON CASCARA",
    "GARBANZA", "GARAPIÑADO", "GOMITA", "LUNETA", "HUEVITO CHOCOLATE",
    "GALLETA MARINA", "CIRUELA", "PASAS", "SEMILLA DE CALABAZA",
    "SEMILLA DE GIRASOL", "NUEZ", "ALMENDRA", "GRANOLA", "CHILE DE ARBOL",
    "CHILE PULLA", "CHILE CASCABEL", "CAMARON", "CAMARON MOLIDO",
    "CHARAL NATURAL", "CHARAL ADOBADO", "CECINA NATURAL", "CECINA ADOBADA",
    "CECINA DE LIMON", "CECINA CHILTEPIN", "CECINA CHIPOTLE",
    "CECINA HABANERO", "CECINA ARTESANAL", "PAPA FRITA",
    "CHURRO DE MASA", "CHURRO DELGADO", "CHICHARRON", "CHICHARRON CRAC",
    "PLATANO", "TOSTADA", "MIEL", "TIRA DE CC MINI", "TIRA DE DULCE",
    "MIX VERDE", "MIX ROJO"
]
ESPECIALES_REPORTE_DIARIO_PT = {
    "ML": {
        "nombre": "Mega Lupita",
        "presentaciones": ["250g", "230g", "60g", "50g", "150g", "40g"]
    },
    "Y": {
        "nombre": "Yeos",
        "presentaciones": ["200g", "180g", "150g", "120g", "60g", "220g", "250g", "100g", "700g", "650g"]
    },
    "YML": {
        "nombre": "Super la merced",
        "presentaciones": ["20g", "70g", "80g", "60g", "65g", "100g", "50g", "45g", "40g", "200g", "150g", "180g", "220g", "500g"]
    },
    "YV": {
        "nombre": "Yeos Victoria",
        "presentaciones": ["200g", "180g", "150g", "220g", "60g", "100g", "250g", "700g", "650g"]
    },
    "JP": {
        "nombre": "Juaquin Perez",
        "presentaciones": ["750g", "250g", "150g"]
    },
    "N": {
        "nombre": "Norma",
        "presentaciones": ["620g", "600g"]
    }
}



@login_required
@requiere_roles("Producto Terminado", "Recursos Humanos")
def reporte_diario_pt_datos(request):
    fecha_texto = request.GET.get("fecha", timezone.localdate().isoformat())
    movimiento = request.GET.get("movimiento", "salidas")
    destino = request.GET.get("destino", "general")
    tipo_producto = request.GET.get("tipo_producto", "normal")
    especial_codigo = request.GET.get("especial", "ML")

    try:
        fecha = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Formato de fecha inválido."}, status=400)

    if movimiento not in ("salidas", "entradas"):
        return JsonResponse({"error": "Movimiento inválido."}, status=400)

    destinos_validos = {"general", "opcion1", "opcion2", "opcion3", "opcion4"}
    if movimiento == "salidas" and destino not in destinos_validos:
        return JsonResponse({"error": "Destino inválido."}, status=400)

    if tipo_producto not in ("normal", "especial"):
        return JsonResponse({"error": "Tipo de producto inválido."}, status=400)

    if tipo_producto == "especial":
        if especial_codigo not in ESPECIALES_REPORTE_DIARIO_PT:
            return JsonResponse({"error": "Tienda especial inválida."}, status=400)

        especial = ESPECIALES_REPORTE_DIARIO_PT[especial_codigo]
        presentaciones = especial["presentaciones"]
        nombre_especial = especial["nombre"]
    else:
        especial_codigo = None
        nombre_especial = None
        presentaciones = ORDEN_PRESENTACIONES_REPORTE_DIARIO_PT

    if movimiento == "entradas":
        detalles = DetalleEntradaPTerminado.objects.filter(
            entrada_p_terminado__fecha_entrada__date=fecha
        )
    else:
        detalles = DetalleSalidaPTerminado.objects.filter(
            salida_p_terminado__fecha_salida__date=fecha
        )

        if destino != "general":
            detalles = detalles.filter(
                salida_p_terminado__destino=destino
            )

    # Separación entre productos normales y especiales.
    if tipo_producto == "especial":
        detalles = detalles.filter(
            producto_variacion__producto__nombre__startswith=f"{especial_codigo} "
        )
    else:
        filtro_especiales = Q()

        for codigo in ESPECIALES_REPORTE_DIARIO_PT:
            filtro_especiales |= Q(
                producto_variacion__producto__nombre__startswith=f"{codigo} "
            )

        detalles = detalles.exclude(filtro_especiales)

    movimientos = (
        detalles.values(
            "producto_variacion__producto_id",
            "producto_variacion__producto__nombre",
            "producto_variacion__presentacion__nombre"
        )
        .annotate(total=Sum("cantidad"))
        .order_by()
    )

    mapa_productos = {}
    cero = Decimal("0.00")

    for movimiento_item in movimientos:
        producto_id = movimiento_item["producto_variacion__producto_id"]
        nombre_producto = movimiento_item["producto_variacion__producto__nombre"]
        nombre_presentacion = movimiento_item["producto_variacion__presentacion__nombre"]
        cantidad = movimiento_item["total"] or cero

        if nombre_presentacion not in presentaciones:
            continue

        if producto_id not in mapa_productos:
            mapa_productos[producto_id] = {
                "id": producto_id,
                "producto": nombre_producto,
                "cantidades": {p: cero for p in presentaciones},
                "total": cero
            }

        mapa_productos[producto_id]["cantidades"][nombre_presentacion] += cantidad
        mapa_productos[producto_id]["total"] += cantidad

    indice_productos = {
        nombre.strip().upper(): indice
        for indice, nombre in enumerate(ORDEN_PRODUCTOS_REPORTE_DIARIO_PT)
    }

    def clave_orden_producto(item):
        nombre = item["producto"].strip().upper()

        if tipo_producto == "especial":
            prefijo = f"{especial_codigo} "
            if nombre.startswith(prefijo):
                nombre = nombre[len(prefijo):].strip()

        return (
            indice_productos.get(nombre, len(indice_productos)),
            nombre
        )

    productos_ordenados = sorted(
        mapa_productos.values(),
        key=clave_orden_producto
    )

    stocks = {
        (variacion.producto_id, variacion.presentacion.nombre): variacion.stock
        for variacion in ProductoVariacion.objects.select_related(
            "presentacion"
        ).filter(
            producto_id__in=mapa_productos.keys()
        )
    }

    totales_presentaciones = {p: cero for p in presentaciones}
    total_general = cero
    filas = []

    for producto in productos_ordenados:
        cantidades = [
            float(producto["cantidades"][p])
            for p in presentaciones
        ]

        for presentacion in presentaciones:
            totales_presentaciones[presentacion] += producto["cantidades"][presentacion]

        total_general += producto["total"]

        filas.append({
            "id": producto["id"],
            "producto": producto["producto"],
            "cantidades": cantidades,
            "stocks": [
                float(stocks.get((producto["id"], p), cero))
                for p in presentaciones
            ],
            "variaciones_existentes": [
                (producto["id"], p) in stocks
                for p in presentaciones
            ],
            "total": float(producto["total"])
        })

    return JsonResponse({
        "fecha": fecha.isoformat(),
        "movimiento": movimiento,
        "destino": destino if movimiento == "salidas" else None,
        "tipo_producto": tipo_producto,
        "especial": especial_codigo,
        "nombre_especial": nombre_especial,
        "presentaciones": presentaciones,
        "productos": filas,
        "totales_presentaciones": [
            float(totales_presentaciones[p])
            for p in presentaciones
        ],
        "total_general": float(total_general)
    })


import re

def identificar_ruta_salida(salida):
    if salida.destino == "opcion1":
        return 8 if salida.ruta_id == 8 else None

    if salida.destino != "opcion4":
        return None

    nota = salida.nota or ""
    coincidencias = re.findall(r"\bruta\s*0?(1[01]|[1-9])\b", nota, re.IGNORECASE)
    rutas = set(map(int, coincidencias))

    if len(rutas) == 1:
        return rutas.pop()

    return None

def identificar_ruta_reporte(salida):
    if salida.destino == "opcion1":
        return 8 if salida.ruta_id == 8 else None
    if salida.destino != "opcion4":
        return None

    nota = salida.nota or ""
    rutas = {int(n) for n in re.findall(r"\bruta\s*0?(1[01]|[1-9])\b", nota, re.I)}
    if re.search(r"\brutas?\b", nota, re.I) and re.search(r"\b(?:son|cada)\b", nota, re.I):
        return None
    if re.search(r"\bruta\s*(?:que\s+son\s+la\s+)?\d+\s*,\s*\d+", nota, re.I):
        return None
    if len(rutas) != 1:
        return None
    numero = next(iter(rutas))
    return numero if numero != 8 else None


def obtener_datos_reporte_rutas(inicio, fin):
    salidas = SalidaPTerminado.objects.filter(
        fecha_salida__date__range=(inicio, fin),
        destino__in=["opcion1", "opcion4"]
    ).prefetch_related(
        "detallesalida pterminado_set"
    )


def obtener_datos_reporte_rutas(inicio, fin):
    salidas = SalidaPTerminado.objects.filter(
        fecha_salida__date__range=(inicio, fin),
        destino__in=["opcion1", "opcion4"]
    ).values("id", "destino", "ruta_id", "nota")

    rutas_salidas = {n: [] for n in range(1, 12)}
    sin_identificar = []

    for salida in salidas:
        class SalidaTemporal:
            pass
        obj = SalidaTemporal()
        obj.destino = salida["destino"]
        obj.ruta_id = salida["ruta_id"]
        obj.nota = salida["nota"]
        numero = identificar_ruta_reporte(obj)
        if numero:
            rutas_salidas[numero].append(salida["id"])
        elif salida["destino"] == "opcion4":
            sin_identificar.append(salida["id"])

    ids = [id_salida for lista in rutas_salidas.values() for id_salida in lista]
    detalles = DetalleSalidaPTerminado.objects.filter(
        salida_p_terminado_id__in=ids
    ).values(
        "salida_p_terminado_id",
        "producto_variacion__producto__nombre",
        "producto_variacion__presentacion__nombre"
    ).annotate(cantidad_total=Sum("cantidad"))

    indice = {nombre.upper(): i for i, nombre in enumerate(ORDEN_PRODUCTOS_REPORTE_DIARIO_PT)}
    datos = {n: defaultdict(lambda: defaultdict(lambda: Decimal("0"))) for n in range(1, 12)}
    ruta_por_salida = {sid: n for n, lista in rutas_salidas.items() for sid in lista}

    for detalle in detalles:
        ruta = ruta_por_salida[detalle["salida_p_terminado_id"]]
        nombre = detalle["producto_variacion__producto__nombre"]
        presentacion = detalle["producto_variacion__presentacion__nombre"]
        datos[ruta][nombre][presentacion] += detalle["cantidad_total"] or Decimal("0")

    resultado = {}
    for ruta in range(1, 12):
        grupos = []
        configuraciones = [("Normal", None, ORDEN_PRESENTACIONES_REPORTE_DIARIO_PT)]
        configuraciones += [(v["nombre"], k, v["presentaciones"]) for k, v in ESPECIALES_REPORTE_DIARIO_PT.items()]

        for titulo, prefijo, presentaciones in configuraciones:
            productos = []
            for nombre, cantidades in datos[ruta].items():
                codigo = next((c for c in ESPECIALES_REPORTE_DIARIO_PT if nombre.upper().startswith(c + " ")), None)
                if codigo != prefijo:
                    continue
                valores = [cantidades[p] for p in presentaciones]
                if not any(valores):
                    continue
                nombre_orden = nombre[len(prefijo)+1:] if prefijo else nombre
                productos.append({"nombre": nombre, "valores": valores, "total": sum(valores), "orden": indice.get(nombre_orden.upper(), len(indice))})

            productos.sort(key=lambda p: (p["orden"], p["nombre"]))
            if productos:
                grupos.append({
                    "titulo": titulo,
                    "presentaciones": presentaciones,
                    "productos": productos,
                    "totales": [sum(p["valores"][i] for p in productos) for i in range(len(presentaciones))],
                    "total": sum(p["total"] for p in productos)
                })
        resultado[ruta] = grupos

    return resultado, sin_identificar


@login_required
@requiere_roles("Administrador", "Producto Terminado", "Recursos Humanos")
def reporte_semanal_rutas_html(request):
    hoy = timezone.localdate()
    return render(request, "ProductoTerminado/reportes/reporte_semanal_rutas.html", {
        "fecha_inicio": (hoy - timedelta(days=6)).isoformat(),
        "fecha_fin": hoy.isoformat()
    })


@login_required
@requiere_roles("Administrador", "Producto Terminado", "Recursos Humanos")
def reporte_semanal_rutas_pdf(request):
    try:
        inicio = datetime.strptime(request.GET["inicio"], "%Y-%m-%d").date()
        fin = datetime.strptime(request.GET["fin"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return HttpResponseBadRequest("Fechas inválidas.")
    if inicio > fin:
        return HttpResponseBadRequest("La fecha inicial no puede ser posterior a la final.")

    datos, sin_identificar = obtener_datos_reporte_rutas(inicio, fin)
    buffer = io.BytesIO()
    #documento = SimpleDocTemplate(buffer, pagesize=landscape(A3), rightMargin=12*mm, leftMargin=12*mm, topMargin=14*mm, bottomMargin=14*mm)
    documento = SimpleDocTemplate(buffer, pagesize=A3, rightMargin=10*mm, leftMargin=10*mm, topMargin=14*mm, bottomMargin=14*mm)
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("TituloRuta", parent=estilos["Heading2"], fontSize=13, spaceAfter=10)
    celda = ParagraphStyle("CeldaRuta", fontSize=7, leading=9)
    celda_encabezado = ParagraphStyle("CeldaEncabezadoRuta", parent=celda, textColor=colors.white, fontName="Helvetica-Bold")
    elementos = [
        Paragraph("OSMIT - REPORTE SEMANAL DE SALIDAS POR RUTA", estilos["Title"]),
        Paragraph(f"Periodo: {inicio:%d/%m/%Y} al {fin:%d/%m/%Y}", estilos["Normal"]),
        Spacer(1, 12)
    ]

    def numero(valor):
        return f"{valor:,.2f}".rstrip("0").rstrip(".")

    for ruta in range(1, 12):
        if ruta > 1:
            elementos.append(PageBreak())
        elementos.append(Paragraph(f"RUTA {ruta}", titulo))
        grupos = datos[ruta]
        if not grupos:
            elementos.append(Paragraph("Sin salidas registradas en este periodo.", estilos["Normal"]))
            continue

        for grupo in grupos:
            elementos.append(Paragraph(f"Productos: {escape(grupo['titulo'])}", estilos["Heading3"]))
            encabezado = ["Producto"] + grupo["presentaciones"] + ["Total"]
            filas = [[Paragraph(escape(str(h)), celda_encabezado) for h in encabezado]]

            for producto in grupo["productos"]:
                filas.append(
                    [Paragraph(escape(producto["nombre"]), celda)] +
                    [numero(v) if v else "-" for v in producto["valores"]] +
                    [numero(producto["total"])]
                )

            filas.append(["TOTAL GENERAL"] + [numero(v) for v in grupo["totales"]] + [numero(grupo["total"])])
            ancho = A3[0] - 20*mm
            ancho_producto = 42*mm
            #ancho = landscape(A3)[0] - 24*mm
            #ancho_producto = 52*mm
            ancho_otras = (ancho - ancho_producto) / (len(encabezado)-1)
            tabla = Table(filas, colWidths=[ancho_producto] + [ancho_otras]*(len(encabezado)-1), repeatRows=1, hAlign="LEFT")
            tabla.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#343a40")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e9ecef")),
                ("BACKGROUND", (-1,1), (-1,-2), colors.HexColor("#e9eff5")),
                ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#cbd1d7")),
                ("FONTSIZE", (0,0), (-1,-1), 7),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ALIGN", (1,1), (-1,-1), "CENTER"),
                ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 6)
            ]))
            elementos.append(tabla)
            elementos.append(Spacer(1, 14))

    if sin_identificar:
        elementos.append(PageBreak())
        elementos.append(Paragraph("SALIDAS DE OTROS SIN RUTA IDENTIFICADA", titulo))
        elementos.append(Paragraph(f"Se encontraron {len(sin_identificar)} salidas para revisión. No se sumaron a las rutas.", estilos["Normal"]))
        for salida in SalidaPTerminado.objects.filter(id__in=sin_identificar).order_by("fecha_salida"):
            elementos.append(Paragraph(f"Salida #{salida.id} - {escape(salida.nota or '(Sin nota)')}", estilos["Normal"]))

    documento.build(elementos)
    buffer.seek(0)
    respuesta = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    respuesta["Content-Disposition"] = f'attachment; filename="salidas_rutas_{inicio}_{fin}.pdf"'
    return respuesta







# ''''''''''''''''''''''''''''''''''''''''''''PARA EL DASHBOARD Graficas

from datetime import timedelta,datetime
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
        .filter(
            salida_p_terminado__fecha_salida__date__range=(hace_7_dias, hoy)
        )
        .values(
            'producto_variacion__producto__nombre',
            'producto_variacion__presentacion__nombre'
        )
        .annotate(total_salidas=Sum('cantidad'))
        .order_by('-total_salidas')[:5]
    )

    labels = [
        f"{item['producto_variacion__producto__nombre']} "
        f"({item['producto_variacion__presentacion__nombre']})"
        for item in productos_top
    ]

    data = [
        float(item['total_salidas'])
        for item in productos_top
    ]

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


