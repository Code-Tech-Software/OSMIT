from . import models
from .models import PedidoProduccion, DetallePedidoProduccion, ProductoGranel, SalidaGranel, DetalleSalidaGranel, Lote, \
    EntradaGranel, DetalleEntradaGranel, DevolucionGranel, DetalleDevolucionGranel, DetalleCorteInventarioGranel, \
    CorteInventarioGranel, CategoriaProducto, Proveedor
from .forms import ProductoGranelForm, SalidaGranelForm, PedidoProduccionForm, DevolucionGranelForm, \
    CorteInventarioForm, CategoriaProductoForm, ProveedorForm
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ProductoGranel
from .forms import ProductoGranelForm


# REGISTRO DE ENTRADAS

@login_required
def agregar_producto_granel(request):
    """
    Vista para agregar un nuevo producto a granel.
    Si se ingresa stock inicial mayor a cero, se crea una EntradaGranel y su DetalleEntradaGranel,
    además de generar un lote con fecha de caducidad calculada.
    """
    if request.method == "POST":
        form = ProductoGranelForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            # Si se ingresó stock inicial, se crea la entrada correspondiente
            if producto.stock > 0:
                entrada = EntradaGranel.objects.create(
                    usuario=request.user,
                    nota="Creación de producto con stock inicial"
                )
                DetalleEntradaGranel.objects.create(
                    entrada_granel=entrada,
                    producto_granel=producto,
                    cantidad=producto.stock
                )
                # Se crea el lote correspondiente
                fecha_entrada = timezone.now()
                fecha_caducidad = (fecha_entrada + timedelta(days=producto.tiempo_caducidad)).date()
                Lote.objects.create(
                    producto_granel=producto,
                    cantidad=producto.stock,
                    fecha_entrada=fecha_entrada,
                    fecha_caducidad=fecha_caducidad
                )
            messages.success(request, "Producto agregado correctamente.")
            return redirect('listar_productos_granel')
    else:
        form = ProductoGranelForm()
    return render(request, 'ProductoGranel/agregar_producto_granel.html', {'form': form})



@login_required
def registrar_entrada(request):
    productos = ProductoGranel.objects.filter(estado=True)

    if request.method == "POST":
        nota = request.POST.get('nota', '')
        cantidades_validas = []

        # Validar que al menos una cantidad sea mayor a cero
        for producto in productos:
            cantidad_str = request.POST.get(f'cantidad_{producto.id}', '0')
            try:
                cantidad = Decimal(cantidad_str)
            except Exception:
                cantidad = Decimal('0')
            if cantidad > 0:
                cantidades_validas.append((producto, cantidad))

        if not cantidades_validas:
            messages.error(request, "Debes ingresar al menos una cantidad mayor a 0.")
            return render(request, 'ProductoGranel/entradas/registrar_entrada.html', {'productos': productos})

        # Crear la entrada porque sí hay cantidades válidas
        entrada = EntradaGranel.objects.create(
            usuario=request.user,
            nota=nota
        )

        fecha_entrada = timezone.now()
        for producto, cantidad in cantidades_validas:
            DetalleEntradaGranel.objects.create(
                entrada_granel=entrada,
                producto_granel=producto,
                cantidad=cantidad
            )
            producto.stock += cantidad
            producto.save()

            fecha_caducidad = (fecha_entrada + timedelta(days=producto.tiempo_caducidad)).date()
            Lote.objects.create(
                producto_granel=producto,
                cantidad=cantidad,
                fecha_entrada=fecha_entrada,
                fecha_caducidad=fecha_caducidad
            )

        messages.success(request, "Entrada registrada exitosamente.")
        return redirect('registrar_entrada')

    return render(request, 'ProductoGranel/entradas/registrar_entrada.html', {'productos': productos})

# -----------------------SALIDA


@login_required
def registrar_salida(request):
    """
    Vista para registrar una salida de productos.
    Se muestran todos los productos activos y, junto a cada uno, un campo para ingresar la cantidad a retirar.
    Se verifica que no se retire más de lo disponible.
    Se utiliza el método FIFO para determinar de qué lote proviene cada salida y se actualizan los lotes:
      - Si la cantidad solicitada supera el stock, se aborta la operación.
      - Si un lote llega a 0, se marca como 'agotado' inmediatamente.
    """
    productos = ProductoGranel.objects.filter(estado=True)

    if request.method == "POST":
        salida_form = SalidaGranelForm(request.POST)
        cantidades = {}  # Guardará las cantidades solicitadas por producto

        # Verificar que las cantidades solicitadas no excedan el stock de cada producto (sólo considerando lotes activos)
        error = False
        for producto in productos:
            cantidad_str = request.POST.get(f'cantidad_{producto.id}', '0')
            try:
                cantidad = Decimal(cantidad_str)
            except Exception:
                cantidad = Decimal('0')

            if cantidad > 0:
                # Calcular el stock disponible solo en lotes activos
                stock_activo = Lote.objects.filter(
                    producto_granel=producto,
                    estado_lote='activo'
                ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')

                if cantidad > stock_activo:
                    messages.error(
                        request,
                        f"No hay stock suficiente para {producto.nombre}. Stock actual (lotes activos): {stock_activo}"
                    )
                    error = True
                else:
                    cantidades[producto.id] = cantidad

        if error:
            return render(request, 'ProductoGranel/salidas/salida_granel.html',
                          {'salida_form': salida_form, 'productos': productos})

        if salida_form.is_valid():
            salida = salida_form.save(commit=False)
            salida.usuario = request.user
            salida.fecha_salida = timezone.now()
            salida.save()

            productos_procesados = False  # Bandera para saber si se procesó al menos un producto

            # Procesar la salida para cada producto que tenga cantidad solicitada
            for producto in productos:
                cantidad = cantidades.get(producto.id, Decimal('0'))
                if cantidad > 0:
                    cantidad_restante = cantidad
                    # Se obtienen los lotes activos ordenados por fecha de entrada (FIFO)
                    lotes = Lote.objects.filter(
                        producto_granel=producto,
                        estado_lote='activo'
                    ).order_by('fecha_entrada')

                    for lote in lotes:
                        if cantidad_restante <= 0:
                            break

                        # Si el lote tiene suficiente cantidad para cubrir la cantidad restante
                        if lote.cantidad >= cantidad_restante:
                            lote.cantidad -= cantidad_restante
                            # Si el lote queda en 0, se marca inmediatamente como agotado
                            if lote.cantidad == Decimal('0'):
                                lote.estado_lote = 'agotado'
                            lote.save()
                            DetalleSalidaGranel.objects.create(
                                salida_granel=salida,
                                producto_granel=producto,
                                lote=lote,
                                cantidad=cantidad_restante
                            )
                            cantidad_restante = Decimal('0')
                        else:
                            # Si el lote no tiene suficiente cantidad, se utiliza todo el lote
                            cantidad_a_usar = lote.cantidad
                            cantidad_restante -= cantidad_a_usar
                            lote.cantidad = Decimal('0')
                            lote.estado_lote = 'agotado'
                            lote.save()
                            DetalleSalidaGranel.objects.create(
                                salida_granel=salida,
                                producto_granel=producto,
                                lote=lote,
                                cantidad=cantidad_a_usar
                            )

                    # Actualizar el stock del producto recalculándolo a partir de los lotes activos
                    nuevo_stock = Lote.objects.filter(
                        producto_granel=producto,
                        estado_lote='activo'
                    ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
                    producto.stock = nuevo_stock
                    producto.save()
                    productos_procesados = True

            if productos_procesados:
                messages.success(request, "Salida registrada correctamente.")
                return redirect('registrar_salida')  # Asegúrate de tener definida la ruta
            else:
                salida.delete()
                messages.error(request, "No se registró ninguna salida, revisa las cantidades ingresadas.")

    else:
        salida_form = SalidaGranelForm()

    return render(request, 'ProductoGranel/salidas/salida_granel.html',
                  {'salida_form': salida_form, 'productos': productos})


@login_required
def registrar_pedido_produccion(request):
    """
    Vista para registrar un PedidoProduccion.
    Se listan los productos disponibles y se permite ingresar la cantidad solicitada para cada uno.
    Antes de guardar, se valida que la cantidad solicitada no exceda el stock actual.
    Al enviar, se crea un PedidoProduccion con estado 'pendiente' y se registran los detalles.
    """
    productos = ProductoGranel.objects.filter(estado=True)

    if request.method == "POST":
        pedido_form = PedidoProduccionForm(request.POST)
        cantidades = {}  # Almacena la cantidad solicitada para cada producto

        error = False  # Bandera para detectar errores de cantidad
        for producto in productos:
            cantidad_str = request.POST.get(f'cantidad_{producto.id}', '0')
            try:
                cantidad = Decimal(cantidad_str)
            except Exception:
                cantidad = Decimal('0')
            # Si se ingresó cantidad mayor a cero, se valida contra el stock actual
            if cantidad > 0:
                if cantidad > producto.stock:
                    messages.error(
                        request,
                        f"Para el producto {producto.nombre} la cantidad solicitada ({cantidad}) supera el stock disponible ({producto.stock})."
                    )
                    error = True
                else:
                    cantidades[producto.id] = cantidad

        # Si ningún producto tiene cantidad o hay errores, se muestra mensaje y se vuelve a renderizar
        if error or not cantidades:
            if not cantidades and not error:
                messages.error(request, "Debes ingresar al menos una cantidad mayor a 0 para algún producto.")
            return render(request, 'ProductoGranel/pedidos/pedido_produccion.html',
                          {'pedido_form': pedido_form, 'productos': productos})

        if pedido_form.is_valid():
            pedido = pedido_form.save(commit=False)
            pedido.usuario = request.user
            pedido.fecha_pedido = timezone.now()
            pedido.estado = 'pendiente'
            pedido.procesado = False
            pedido.save()

            # Crear los detalles del pedido para cada producto que tenga cantidad ingresada
            for producto in productos:
                cantidad = cantidades.get(producto.id, Decimal('0'))
                if cantidad > 0:
                    DetallePedidoProduccion.objects.create(
                        pedido_produccion=pedido,
                        producto_granel=producto,
                        usuario=request.user,
                        cantidad=cantidad
                    )
            messages.success(request, "Pedido de producción registrado correctamente en estado 'pendiente'.")
            return redirect('registrar_pedido_produccion')  # Ajusta la ruta según tu proyecto
    else:
        pedido_form = PedidoProduccionForm()

    return render(request, 'ProductoGranel/pedidos/pedido_produccion.html',
                  {'pedido_form': pedido_form, 'productos': productos})


@login_required
def lista_pedidos(request):
    """
    Vista para listar los pedidos de producción.
    Se muestran todos los pedidos ordenados por fecha, de modo que los más recientes aparezcan primero.
    """
    pedidos = PedidoProduccion.objects.all().order_by('-fecha_pedido')
    return render(request, 'ProductoGranel/pedidos/lista_pedidos.html', {'pedidos': pedidos})


@login_required
def aceptar_pedido_produccion(request, pedido_id):
    """
    Vista para aceptar un pedido de producción sin modificar los modelos.
    Se valida que exista stock suficiente en los lotes activos para cada producto, se descuenta utilizando
    la lógica FIFO (por lotes) y se registra la salida correspondiente.
    Finalmente, se actualiza el pedido a 'en_produccion' y se marca como procesado.
    """
    pedido = get_object_or_404(PedidoProduccion, id=pedido_id)

    # Solo se procesan pedidos pendientes
    if pedido.estado != 'pendiente':
        messages.error(request, "Solo se pueden aceptar pedidos en estado pendiente.")
        return redirect('lista_pedidos')

    detalles = pedido.detallepedidoproduccion_set.all()

    # Verificar stock de cada detalle utilizando solo los lotes activos
    for detalle in detalles:
        stock_activo = Lote.objects.filter(
            producto_granel=detalle.producto_granel,
            estado_lote='activo'
        ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
        if detalle.cantidad > stock_activo:
            messages.error(
                request,
                f"Stock insuficiente para {detalle.producto_granel.nombre} en lotes activos. Stock actual: {stock_activo}"
            )
            return redirect('lista_pedidos')

    try:
        with transaction.atomic():
            # Registrar la salida asociada al pedido
            salida = SalidaGranel.objects.create(
                usuario=request.user,
                destino="Produccion",
                nota=f"Salida generada por pedido de producción {pedido.id}",
                fecha_salida=timezone.now()
            )

            for detalle in detalles:
                producto = detalle.producto_granel
                cantidad_a_descontar = detalle.cantidad

                # Obtener los lotes activos ordenados por fecha de entrada (FIFO)
                lotes = Lote.objects.filter(
                    producto_granel=producto,
                    estado_lote='activo'
                ).order_by('fecha_entrada')

                for lote in lotes:
                    if cantidad_a_descontar <= Decimal('0'):
                        break

                    cantidad_del_lote = min(cantidad_a_descontar, lote.cantidad)
                    lote.cantidad -= cantidad_del_lote

                    # Si el lote queda en cero, actualizar el estado a 'agotado'
                    if lote.cantidad == Decimal('0'):
                        lote.estado_lote = 'agotado'
                    lote.save()

                    # Registrar detalle de salida
                    DetalleSalidaGranel.objects.create(
                        salida_granel=salida,
                        producto_granel=producto,
                        lote=lote,
                        cantidad=cantidad_del_lote
                    )
                    cantidad_a_descontar -= cantidad_del_lote

                # Actualizar el stock total del producto basado en los lotes activos
                nuevo_stock = Lote.objects.filter(
                    producto_granel=producto,
                    estado_lote='activo'
                ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
                producto.stock = nuevo_stock
                producto.save()

            # Actualizar el pedido: marcarlo como procesado y cambiar el estado
            pedido.estado = 'en_produccion'
            pedido.procesado = True
            pedido.save()

        messages.success(request, f"El pedido {pedido.id} ha sido aceptado y el stock actualizado.")
    except Exception as e:
        messages.error(request, f"Ocurrió un error al procesar el pedido: {str(e)}")
    return redirect('lista_pedidos')


# ----------------------------------------------------------------------------------------------------------------------DEVOLUCIONES



@login_required
def registrar_devolucion(request, salida_id):
    salida = get_object_or_404(SalidaGranel, id=salida_id)
    detalles_salida = salida.detallesalidagranel_set.all()

    # Calcular la cantidad ya devuelta para cada detalle
    for detalle in detalles_salida:
        resultado = DetalleDevolucionGranel.objects.filter(
            devolucion_granel__salida_granel=salida,
            producto_granel=detalle.producto_granel,
            lote=detalle.lote
        ).aggregate(total=Sum('cantidad'))
        detalle.ya_devolvido = resultado['total'] or Decimal('0')

    if request.method == "POST":
        devolucion_form = DevolucionGranelForm(request.POST)
        if devolucion_form.is_valid():
            try:
                with transaction.atomic():
                    cantidades_validas = False
                    detalles_creados = []

                    # Crear la devolución (aún no se guarda)
                    devolucion = devolucion_form.save(commit=False)
                    devolucion.usuario = request.user
                    devolucion.salida_granel = salida
                    devolucion.fecha_devolucion = timezone.now()

                    for detalle in detalles_salida:
                        cantidad_str = request.POST.get(f'cantidad_{detalle.id}', '0')
                        try:
                            cantidad_devolver = Decimal(cantidad_str)
                        except Exception:
                            cantidad_devolver = Decimal('0')

                        if cantidad_devolver <= 0:
                            continue

                        cantidades_validas = True

                        defecto = request.POST.get(f'defecto_{detalle.id}', None) is not None

                        resultado = DetalleDevolucionGranel.objects.filter(
                            devolucion_granel__salida_granel=salida,
                            producto_granel=detalle.producto_granel,
                            lote=detalle.lote
                        ).aggregate(total=Sum('cantidad'))
                        ya_devolvido = resultado['total'] or Decimal('0')

                        cantidad_maxima = detalle.cantidad - ya_devolvido

                        if cantidad_devolver > cantidad_maxima:
                            messages.error(
                                request,
                                f"Para el producto {detalle.producto_granel.nombre} (lote {detalle.lote.id}) "
                                f"solo se puede devolver hasta {cantidad_maxima} {detalle.producto_granel.unidad_medida}."
                            )
                            raise Exception("Cantidad a devolver excede lo permitido.")

                        detalles_creados.append({
                            'detalle': detalle,
                            'cantidad': cantidad_devolver,
                            'defecto': defecto
                        })

                    if not cantidades_validas:
                        messages.error(request, "Debe ingresar al menos una cantidad mayor a 0 para registrar una devolución.")
                        raise Exception("Sin cantidades válidas.")

                    # Guardar devolución principal
                    devolucion.save()

                    # Procesar y guardar los detalles válidos
                    for item in detalles_creados:
                        detalle = item['detalle']
                        cantidad_devolver = item['cantidad']
                        defecto = item['defecto']

                        DetalleDevolucionGranel.objects.create(
                            devolucion_granel=devolucion,
                            usuario=request.user,
                            producto_granel=detalle.producto_granel,
                            lote=detalle.lote,
                            cantidad=cantidad_devolver
                        )

                        if defecto:
                            detalle.lote.estado_lote = 'inspeccion'
                        else:
                            detalle.lote.cantidad += cantidad_devolver
                            if detalle.lote.estado_lote != 'activo':
                                detalle.lote.estado_lote = 'activo'
                            detalle.producto_granel.stock += cantidad_devolver
                            detalle.producto_granel.save()

                        detalle.lote.save()

                    messages.success(request, "Devolución registrada correctamente.")
                    return redirect('lista_salidas')
            except Exception as e:
                messages.error(request, f"Ocurrió un error al registrar la devolución: {str(e)}")
        else:
            messages.error(request, "Corrige los errores en el formulario.")
    else:
        devolucion_form = DevolucionGranelForm()

    context = {
        'salida': salida,
        'detalles_salida': detalles_salida,
        'devolucion_form': devolucion_form,
    }
    return render(request, 'ProductoGranel/devoluciones/registrar_devolucion.html', context)

@login_required
def lista_salidas(request):
    """
    Vista para listar las salidas de productos a granel.
    Desde esta lista se puede acceder a la funcionalidad de devolución.
    """
    salidas = SalidaGranel.objects.all().order_by('-fecha_salida')
    return render(request, 'ProductoGranel/devoluciones/lista_salidas.html', {'salidas': salidas})


# --------------------------------------------------------------------------------------------------------------------------------------------------Corte


@login_required
def realizar_corte(request):
    """
    Vista para realizar el corte de inventario.
    Se listan todos los productos activos y se muestra el stock teórico.
    El operario ingresa el stock real y se calcula la diferencia.
    Si al finalizar el corte ninguna diferencia es encontrada, se marca como 'correcto'.
    De lo contrario, se marca como 'pendiente' (requiere ajuste).
    """
    productos = ProductoGranel.objects.filter(estado=True)

    if request.method == "POST":
        form = CorteInventarioForm(request.POST)
        if form.is_valid():
            # Crear el registro principal del corte
            corte = form.save(commit=False)
            corte.usuario = request.user
            corte.fecha = timezone.now()

            # Inicialmente asumimos que es correcto
            corte.estado = 'correcto'
            corte.save()

            # Variable para determinar si existe alguna diferencia
            requiere_ajuste = False

            # Por cada producto, obtener el stock teórico y el ingresado
            for producto in productos:
                stock_teorico = producto.stock  # stock del sistema
                stock_real_str = request.POST.get(f'stock_real_{producto.id}', '0')
                try:
                    stock_real = Decimal(stock_real_str)
                except Exception:
                    stock_real = Decimal('0')

                diferencia = stock_real - stock_teorico
                ajuste_necesario = diferencia != 0
                if ajuste_necesario:
                    requiere_ajuste = True

                # Crear el detalle del corte para este producto
                DetalleCorteInventarioGranel.objects.create(
                    corte_inventario=corte,
                    producto_granel=producto,
                    stock_teorico=stock_teorico,
                    stock_real=stock_real,
                    diferencia=diferencia,
                    ajuste_necesario=ajuste_necesario
                )

            # Si existe alguna diferencia, marcamos el corte como pendiente para ajuste
            if requiere_ajuste:
                corte.estado = 'pendiente'
                corte.save()

            messages.success(request, "Corte de inventario registrado correctamente.")
            return redirect('lista_cortes')
        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = CorteInventarioForm()

    context = {
        'form': form,
        'productos': productos,
    }
    return render(request, 'ProductoGranel/cortes/realizar_corte.html', context)


@login_required
def lista_cortes(request):
    """
    Vista para listar los cortes de inventario.
    Un corte requiere ajuste si su estado es 'pendiente'.
    """
    cortes = CorteInventarioGranel.objects.all().order_by('-fecha')
    for corte in cortes:
        corte.requiere_ajuste = (corte.estado == 'pendiente')
    context = {
        'cortes': cortes,
    }
    return render(request, 'ProductoGranel/cortes/lista_cortes.html', context)




@login_required
def ajustar_inventario(request, corte_id):
    """
    Vista para ajustar el inventario a partir de un corte de inventario.
    Se recorren los detalles del corte y, para cada producto donde exista diferencia,
    se actualiza el stock real y se reconcilian los lotes activos.
    - Si la suma de las cantidades en los lotes activos es menor que el stock real,
      se suma la diferencia al último lote activo.
    - Si no existen lotes activos, se crea un nuevo lote.
    Finalmente, se marca el corte como 'ajustado'.
    """
    corte = get_object_or_404(CorteInventarioGranel, id=corte_id)
    detalles = corte.detallecorteinventariogranel_set.all()

    if request.method == "POST":
        # Procesar cada detalle del corte
        for detalle in detalles:
            if detalle.diferencia != Decimal('0'):
                producto = detalle.producto_granel
                # Actualizamos el stock del producto al stock real del corte
                producto.stock = detalle.stock_real
                producto.save()

                # Ajustar los lotes activos:
                # Se obtienen los lotes activos para el producto, ordenados por fecha de entrada
                lotes = Lote.objects.filter(producto_granel=producto, estado_lote='activo').order_by('fecha_entrada')
                total_lotes = sum([lote.cantidad for lote in lotes])
                diferencia_lote = detalle.stock_real - total_lotes

                if lotes.exists():
                    # Si hay lotes activos, se ajusta el último lote
                    ultimo_lote = lotes.last()
                    ultimo_lote.cantidad += diferencia_lote
                    ultimo_lote.save()
                else:
                    # Si no hay lotes activos, se crea uno nuevo con la cantidad total
                    fecha_entrada = corte.fecha
                    fecha_caducidad = (fecha_entrada + timedelta(days=producto.tiempo_caducidad)).date()
                    Lote.objects.create(
                        producto_granel=producto,
                        cantidad=detalle.stock_real,
                        fecha_entrada=fecha_entrada,
                        fecha_caducidad=fecha_caducidad,
                        estado=True,
                        estado_lote='activo'
                    )

        corte.estado = 'ajustado'
        corte.save()

        messages.success(request, "Ajuste realizado correctamente.")
        return redirect('lista_cortes')

    context = {
        'corte': corte,
        'detalles': detalles,
    }
    return render(request, 'ProductoGranel/cortes/ajuste_inventario.html', context)


@login_required
def detalle_corte(request, corte_id):
    """
    Vista para mostrar los detalles de un corte de inventario.
    """
    corte = get_object_or_404(CorteInventarioGranel, id=corte_id)
    # Se asume que la relación reversa es 'detallecorteinventariogranel_set'
    detalles = corte.detallecorteinventariogranel_set.all()
    context = {
        'corte': corte,
        'detalles': detalles,
    }
    return render(request, 'ProductoGranel/cortes/detalle_corte.html', context)


@login_required
def listar_productos_granel(request):
    """
    Muestra un listado con todos los productos a granel registrados respetando el swich.
    """
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        productos = ProductoGranel.objects.all()
    else:
        productos = ProductoGranel.objects.filter(estado=True)

    return render(request, 'ProductoGranel/productos/listar_productos.html',{'productos': productos, 'mostrar_todos': mostrar_todos})


@login_required
def editar_producto_granel(request, pk):
    """
    Permite editar un producto a granel existente.
    """
    producto = get_object_or_404(ProductoGranel, pk=pk)
    if request.method == 'POST':
        form = ProductoGranelForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado correctamente.")  # esto para las notificaciones
            return redirect('listar_productos_granel')
    else:
        form = ProductoGranelForm(instance=producto)
    return render(request, 'ProductoGranel/productos/editar_producto.html', {'form': form})


@login_required
def eliminar_producto_granel(request, pk):
    """
    Elimina lógicamente un producto a granel cambiando su estado a False.
    """
    producto = get_object_or_404(ProductoGranel, pk=pk)
    producto.estado = False
    producto.save()
    messages.success(request, "Producto desactivado correctamente.")
    return redirect('listar_productos_granel')




#CATEGORIAS DE PRODUCTOS--------------------------------------------------------------------------------

def lista_categorias(request):

    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        categorias = CategoriaProducto.objects.all()
    else:
        categorias = CategoriaProducto.objects.filter(estado=True)


    return render(request, 'ProductoGranel/categorias/lista.html', {'categorias': categorias,'mostrar_todos': mostrar_todos})

def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoría de Productos creada correctamente.")
            return redirect('lista_categorias')
    else:
        form = CategoriaProductoForm()
    return render(request, 'ProductoGranel/categorias/crear.html', {'form': form})

def editar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProducto, pk=pk)
    form = CategoriaProductoForm(request.POST or None, request.FILES or None, instance=categoria)
    if form.is_valid():
        form.save()
        messages.success(request, "Categoría de Productos actualizada correctamente.")
        return redirect('lista_categorias')
    return render(request, 'ProductoGranel/categorias/editar.html', {'form': form, 'categoria': categoria})

def eliminar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProducto, pk=pk)
    categoria.estado = False
    categoria.save()
    messages.success(request, "Categoría de Productos desactivada correctamente.")
    return redirect('lista_categorias')



#==========-------------------------------------------------------------------------PROVEEDORES DE PRODUCTO A GRANEL#
def lista_proveedores(request):

    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        proveedores = Proveedor.objects.all()
    else:
        proveedores = Proveedor.objects.filter(estado=True)



    return render(request, 'ProductoGranel/proveedores/lista.html', {'proveedores': proveedores,'mostrar_todos': mostrar_todos})

def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Proveedor creado correctamente.")
            return redirect('lista_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'ProductoGranel/proveedores/crear.html', {'form': form})

def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid():
        form.save()
        messages.success(request, "Proveedor actualizado correctamente.")
        return redirect('lista_proveedores')
    return render(request, 'ProductoGranel/proveedores/editar.html', {'form': form, 'proveedor': proveedor})

def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.estado = False
    proveedor.save()
    messages.success(request, "Proveedor desactivado correctamente.")
    return redirect('lista_proveedores')



#''''''''''''''''''''''''''''''''''''''''''''PARA EL DAHBOAR

from django.db.models import Count, Sum
from datetime import timedelta
from django.utils.timezone import now
from django.db.models.functions import TruncDate
from django.http import JsonResponse

def entradas_salidas_por_dia(request):
    hoy = now().date()
    hace_7_dias = hoy - timedelta(days=6)
    dias = [hace_7_dias + timedelta(days=i) for i in range(7)]
    labels = [d.strftime("%d/%m") for d in dias]

    # Entradas por día (sumando cantidades)
    entradas = (
        DetalleEntradaGranel.objects
        .filter(entrada_granel__fecha_entrada__date__range=(hace_7_dias, hoy))
        .annotate(fecha=TruncDate('entrada_granel__fecha_entrada'))
        .values('fecha')
        .annotate(total=Sum('cantidad'))
        .order_by('fecha')
    )

    # Salidas por día (sumando cantidades)
    salidas = (
        DetalleSalidaGranel.objects
        .filter(salida_granel__fecha_salida__date__range=(hace_7_dias, hoy))
        .annotate(fecha=TruncDate('salida_granel__fecha_salida'))
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




def top_productos_mas_utilizados(request):
    # Sumamos cantidad total salida por producto y ordenamos
    productos_top = (
        DetalleSalidaGranel.objects
        .values('producto_granel__nombre')
        .annotate(total_salidas=Sum('cantidad'))
        .order_by('-total_salidas')[:7]
    )

    labels = [item['producto_granel__nombre'] for item in productos_top]
    data = [float(item['total_salidas']) for item in productos_top]

    return JsonResponse({
        'labels': labels,
        'data': data
    })



from django.db.models import F, Sum, DecimalField, ExpressionWrapper
def indicadores_dashboard(request):
    productos_activos = ProductoGranel.objects.filter(estado=True)

    total_productos = productos_activos.count()
    # Productos con stock < stock_min, pero excluyendo los que tienen stock == 0
    productos_bajo_min = productos_activos.filter(
        stock__lt=F('stock_min'),
        stock__gt=0
    ).count()

    # Productos sin stock
    productos_sin_stock = productos_activos.filter(stock=0).count()

    # Pedidos pendientes
    pedidos_pendientes = PedidoProduccion.objects.filter(estado='pendiente').count()

    # Valor total del stock (stock * costo), solo para productos activos
    productos_con_valor = productos_activos.annotate(
        valor_total=ExpressionWrapper(
            F('stock') * F('costo'),
            output_field=DecimalField()
        )
    )
    valor_total_stock = productos_con_valor.aggregate(total=Sum('valor_total'))['total'] or 0

    return JsonResponse({
        'total_productos': total_productos,
        'productos_bajo_min': productos_bajo_min,
        'productos_sin_stock': productos_sin_stock,
        'pedidos_pendientes': pedidos_pendientes,
    })




@login_required
def recursos_humanos_json(request):
    """
    Retorna JSON con lista de productos bajo stock mínimo y sin stock,
    incluyendo datos del proveedor.
    """
    bajo_qs = ProductoGranel.objects.filter(
        estado=True,
        stock__lt=F('stock_min'),
        stock__gt=0
    ).select_related('proveedor', 'categoria_producto')

    sin_qs = ProductoGranel.objects.filter(
        estado=True,
        stock=0
    ).select_related('proveedor', 'categoria_producto')

    def serialize(qs):
        return [
            {
                'nombre': p.nombre,
                'categoria': p.categoria_producto.nombre,
                'stock': float(p.stock),
                'stock_min': float(p.stock_min),
                'proveedor': p.proveedor.nombre,
                'telefono': p.proveedor.telefono or '',
                'correo': p.proveedor.correo or '',
            }
            for p in qs
        ]

    return JsonResponse({
        'bajo_stock': serialize(bajo_qs),
        'sin_stock': serialize(sin_qs),
    }, json_dumps_params={'ensure_ascii': False})