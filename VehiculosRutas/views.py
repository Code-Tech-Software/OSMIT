from django.db import transaction

from ProductoGranel.models import User
from ProductoTerminado.models import Vehiculo, Ruta, Cliente, ClienteDiasVisita, VentaCliente, ConcentradoPedidos, \
    DetalleConcentradoPedidos, DetalleSalidaPTerminado, InventarioRuta, SalidaPTerminado, DetalleVentaCliente, \
    ProductoTerminado
from VehiculosRutas.forms import VehiculoForm, ClienteDiasVisitaForm
from .forms import ClienteForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import RutaForm
from django.contrib import messages
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse



@login_required
def listar_vehiculos(request):
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        vehiculos = Vehiculo.objects.all()
    else:
        vehiculos = Vehiculo.objects.filter(estado=True)

    return render(request, 'VehiculosRutas/vehiculos/listar_vehiculos.html',
                  {'vehiculos': vehiculos, 'mostrar_todos': mostrar_todos})


@login_required
def agregar_vehiculo(request):
    """
    Permite agregar un nuevo vehículo.
    """
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo agregado correctamente.")
            return redirect('listar_vehiculos')
    else:
        form = VehiculoForm()
    return render(request, 'VehiculosRutas/vehiculos/agregar_vehiculo.html', {'form': form})


@login_required
def editar_vehiculo(request, pk):
    """
    Permite editar un vehículo existente.
    """
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado correctamente.")
            return redirect('listar_vehiculos')
    else:
        form = VehiculoForm(instance=vehiculo)
    return render(request, 'VehiculosRutas/vehiculos/editar_vehiculo.html', {'form': form})


@login_required
def eliminar_vehiculo(request, pk):
    """
    Elimina lógicamente un vehículo cambiando su estado a False.
    """
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    vehiculo.estado = False
    vehiculo.save()
    messages.success(request, "Vehículo desactivado correctamente.")
    return redirect('listar_vehiculos')


# ------------------------------------------------RUTAS

@login_required
def listar_rutas(request):


    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        rutas = Ruta.objects.all()
    else:
        rutas = Ruta.objects.filter(estado=True)


    return render(request, 'VehiculosRutas/rutas/listar_rutas.html', {'rutas': rutas, 'mostrar_todos': mostrar_todos})


@login_required
def agregar_ruta(request):
    if request.method == 'POST':
        form = RutaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ruta agregada correctamente.")
            return redirect('listar_rutas')
    else:
        form = RutaForm()
    return render(request, 'VehiculosRutas/rutas/agregar_ruta.html', {'form': form})


@login_required
def editar_ruta(request, pk):
    ruta = get_object_or_404(Ruta, pk=pk)
    if request.method == 'POST':
        form = RutaForm(request.POST, instance=ruta)
        if form.is_valid():
            form.save()
            messages.success(request, "Ruta actualizada correctamente.")
            return redirect('listar_rutas')
    else:
        form = RutaForm(instance=ruta)
    return render(request, 'VehiculosRutas/rutas/editar_ruta.html', {'form': form})


@login_required
def eliminar_ruta(request, pk):
    ruta = get_object_or_404(Ruta, pk=pk)
    ruta.estado = False
    ruta.save()
    messages.success(request, "Ruta desactivada correctamente.")
    return redirect('listar_rutas')


# -------------------------------------------------CLIENTES#



@login_required
def agregar_cliente(request):
    """
    Permite agregar un nuevo cliente.
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente agregado correctamente.")
            return redirect('listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'VehiculosRutas/clientes/agregar_cliente.html', {'form': form})


@login_required
def editar_cliente(request, pk):
    """
    Permite editar un cliente existente.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado correctamente.")
            return redirect('listar_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'VehiculosRutas/clientes/editar_cliente.html', {'form': form})


@login_required
def eliminar_cliente(request, pk):
    """
    Realiza una eliminación lógica del cliente cambiando su estado a False.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.estado = False
    cliente.save()
    messages.success(request, "Cliente desactivado correctamente.")
    return redirect('listar_clientes')


@login_required
def editar_dias_visita(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = ClienteDiasVisitaForm(request.POST)
        if form.is_valid():
            selected_dias = form.cleaned_data['dias']
            # Eliminar los días actuales asignados a este cliente
            ClienteDiasVisita.objects.filter(cliente=cliente).delete()
            # Crear nuevos registros según la selección
            for dia in selected_dias:
                ClienteDiasVisita.objects.create(cliente=cliente, dia_semana=dia)
            return redirect('listar_clientes')
    else:
        # Obtener los días asignados actualmente
        current_days = list(ClienteDiasVisita.objects.filter(cliente=cliente)
                            .values_list('dia_semana', flat=True))
        form = ClienteDiasVisitaForm(initial={'dias': current_days})
    return render(request, 'VehiculosRutas/clientes/editar_dias_visita.html', {'form': form, 'cliente': cliente})

@login_required
def listar_clientes(request):

    ruta_id = request.GET.get('ruta')
    dia = request.GET.get('dia')

    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:

        clientes = Cliente.objects.all()
    else:
        clientes = Cliente.objects.filter(estado=True)

    # Filtrar clientes activos
    #  clientes = Cliente.objects.filter(estado=True)

    if ruta_id == "sin_ruta":
        clientes = clientes.filter(ruta__isnull=True)
    elif ruta_id:
        clientes = clientes.filter(ruta__id=ruta_id)

    if dia == "sin_dia":
        clientes = clientes.filter(clientediasvisita__isnull=True)
    elif dia:
        clientes = clientes.filter(clientediasvisita__dia_semana=dia)

    clientes = clientes.distinct()
    rutas = Ruta.objects.all()
    dias = ClienteDiasVisita.DIAS

    return render(request, 'VehiculosRutas/clientes/listar_clientes.html', {
        'clientes': clientes,
        'rutas': rutas,
        'dias': dias,
        'selected_ruta': ruta_id,
        'selected_dia': dia,
        'mostrar_todos': mostrar_todos
    })


def descargar_clientes_pdf(request):
    ruta = request.GET.get('ruta')
    dia = request.GET.get('dia')

    # Normaliza valores inválidos (como 'None' o vacío) a None real
    ruta = ruta if ruta not in [None, '', 'None'] else None
    dia = dia if dia not in [None, '', 'None'] else None


    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        clientes = Cliente.objects.all()
    else:
        clientes = Cliente.objects.filter(estado=True)

    nombre_ruta = "Todas"
    # Filtrado por ruta
    if ruta == "sin_ruta":
        clientes = clientes.filter(ruta__isnull=True)
        nombre_ruta = "Sin Ruta"
    elif ruta and ruta != "todas":
        try:
            clientes = clientes.filter(ruta__id=int(ruta))
            ruta_obj = Ruta.objects.filter(id=ruta).first()
            if ruta_obj:
                nombre_ruta = ruta_obj.nombre
        except ValueError:
            return HttpResponse('ID de ruta inválido', status=400)

    # Filtrado por día
    if dia == "sin_dia":
        clientes = clientes.exclude(clientediasvisita__isnull=False)
        dia = "Sin día"
    elif not dia or dia == "todos":
        dia = "Todos"
    else:
        clientes = clientes.filter(clientediasvisita__dia_semana=dia)

    # Renderizado de PDF
    template_path = 'VehiculosRutas/clientes/pdf_clientes.html'
    context = { 'mostrar_todos': mostrar_todos,
        'clientes': clientes,
        'ruta': nombre_ruta,
        'dia': dia,

    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="clientes.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Ocurrió un error al generar el PDF', status=500)

    return response

from django.shortcuts import render, get_object_or_404

def venta_cliente_detalle(request, venta_id):
    venta = get_object_or_404(VentaCliente, id=venta_id)
    detalles = list(DetalleVentaCliente.objects.filter(venta_cliente=venta))
    # Calculamos el total en Python y lo añadimos como atributo
    for det in detalles:
        det.total = det.cantidad * det.precio_unitario
    return render(request, 'VehiculosRutas/ventas/venta_cliente_detalle.html', {
        'venta': venta,
        'detalles': detalles
    })
def lista_ventas_cliente(request):
    ventas = VentaCliente.objects.select_related('cliente', 'usuario').order_by('-fecha_venta')
    return render(request, 'VehiculosRutas/ventas/lista_ventas_cliente.html', {
        'ventas': ventas
    })






from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate




from django.db.models.functions import TruncDate
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
def ventas_por_dia(request):
    qs = (
        DetalleVentaCliente.objects
        .annotate(dia=TruncDate('venta_cliente__fecha_venta'))
        .values(
            'dia',
            'venta_cliente__usuario',
            'venta_cliente__usuario__first_name',
        )
        .annotate(
            total_productos=Sum('cantidad'),
            total_ventas=Count('venta_cliente', distinct=True),
            ventas_no_procesadas=Count(
                'venta_cliente',
                filter=Q(venta_cliente__stock_descontado=False),
                distinct=True
            ),
            total_dinero=ExpressionWrapper(
                Sum(F('cantidad') * F('precio_unitario')),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
        .order_by('-dia', 'venta_cliente__usuario__first_name')
    )
    return render(request, 'VehiculosRutas/ventas/ventas_por_dia.html', {
        'grupos': qs
    })


def detalle_ventas_dia(request, fecha, user_id):
    # Para la fecha y el usuario indicados, sumamos por producto
    detalles = (
        DetalleVentaCliente.objects
        .filter(
            venta_cliente__usuario__id=user_id,
            venta_cliente__fecha_venta__date=fecha
        )
        .values('producto_terminado__nombre','producto_terminado__gramaje_producto_terminado__nombre','producto_terminado__presentacion_producto_terminado__nombre')

        .annotate(cantidad_total=Sum('cantidad'))
        .order_by('-cantidad_total')
    )
    # Sacamos el username para mostrar
    username = detalles and request.user.__class__.objects.get(id=user_id).username or ''
    usuario = User.objects.get(id=user_id)

    return render(request, 'VehiculosRutas/ventas/detalle_ventas_dia.html', {
        'fecha': fecha,
        'usuario': usuario,
        'detalles': detalles,
        'user_id': user_id,
    })


from django.db.models import Sum, F

def procesar_ventas_dia(request, fecha, user_id):
    if request.method != 'POST':
        return redirect('detalle_ventas_dia', fecha=fecha, user_id=user_id)

    # Obtener ventas pendientes de procesar
    ventas = VentaCliente.objects.filter(
        usuario__id=user_id,
        fecha_venta__date=fecha,
        stock_descontado=False
    )

    if not ventas.exists():
        messages.error(request, "Ya se procesó el stock para este día.")
        return redirect('detalle_ventas_dia', fecha=fecha, user_id=user_id)

    # Agregar detalles
    detalles = (
        DetalleVentaCliente.objects
        .filter(venta_cliente__in=ventas)
        .values('producto_terminado')
        .annotate(total=Sum('cantidad'))
    )

    # Validar stock
    insuf = []
    for d in detalles:
        prod = ProductoTerminado.objects.get(pk=d['producto_terminado'])
        if prod.stock < d['total']:
            insuf.append(f"{prod.nombre} (stock: {prod.stock}, necesita: {d['total']})")

    if insuf:
        messages.error(request,
            "Stock insuficiente para: " + "; ".join(insuf))
        return redirect('detalle_ventas_dia', fecha=fecha, user_id=user_id)

    # Descontar y marcar ventas
    with transaction.atomic():
        # resto de stock
        for d in detalles:
            ProductoTerminado.objects.select_for_update().filter(
                pk=d['producto_terminado']
            ).update(stock=F('stock') - d['total'])

        # marco las ventas como procesadas
        ventas.update(stock_descontado=True)

    messages.success(request, "Venta procesada y stock descontado.")
    return redirect('detalle_ventas_dia', fecha=fecha, user_id=user_id)
