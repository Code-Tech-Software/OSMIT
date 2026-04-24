from django.db import transaction

from ProductoGranel.models import User
from ProductoTerminado.models import Vehiculo, Ruta, Cliente, ClienteDiasVisita, DetalleSalidaPTerminado, InventarioRuta, SalidaPTerminado
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

import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def clientes_data(request):
    # Parámetros de DataTables
    draw   = int(request.GET.get('draw', 1))
    start  = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()

    # Filtros personalizados
    ruta_id = request.GET.get('ruta')
    dia     = request.GET.get('dia')
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    qs = Cliente.objects.all()
    if not mostrar_todos:
        qs = qs.filter(estado=True)

    if ruta_id == "sin_ruta":
        qs = qs.filter(ruta__isnull=True)
    elif ruta_id:
        qs = qs.filter(ruta__id=ruta_id)

    if dia == "sin_dia":
        qs = qs.filter(clientediasvisita__isnull=True)
    elif dia:
        qs = qs.filter(clientediasvisita__dia_semana=dia)

    # Búsqueda global por nombre o negocio
    if search_value:
        qs = qs.filter(
            Q(nombre__icontains=search_value) |
            Q(nombre_negocio__icontains=search_value) |
            Q(direccion__icontains=search_value) |
            Q(telefono__icontains=search_value)
        )

    total_records    = qs.count()
    qs = qs.distinct().order_by('nombre')[start:start+length]

    # Para evitar N+1
    qs = qs.prefetch_related('clientediasvisita_set', 'ruta')

    data = []
    for cliente in qs:
        # Compongo los días de visita
        dias = cliente.clientediasvisita_set.all()
        if dias:
            lista_dias = ", ".join(d.get_dia_semana_display() for d in dias)
        else:
            lista_dias = "No asignados"

        # Renderizo los botones de acciones desde un partial
        acciones_html = render_to_string('VehiculosRutas/clientes/_acciones.html',
                                         {'cliente': cliente},
                                         request=request)

        data.append({
            'nombre'       : cliente.nombre,
            'nombre_negocio': cliente.nombre_negocio,
            'direccion'    : cliente.direccion,
            'telefono'     : cliente.telefono,
            'ruta'         : cliente.ruta.nombre if cliente.ruta else '',
            'dias_visita'  : lista_dias,
            'estado'       : '<span class="badge bg-custom-success">Activo</span>'
                              if cliente.estado
                              else '<span class="badge bg-custom-danger">Inactivo</span>',
            'acciones'     : acciones_html,
        })

    return JsonResponse({
        'draw'            : draw,
        'recordsTotal'    : total_records,
        'recordsFiltered' : total_records,
        'data'            : data
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

