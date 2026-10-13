from django.db import transaction

from ProductoGranel.models import User
from ProductoTerminado.models import Vehiculo, Ruta, Cliente, ClienteDiasVisita, DetalleSalidaPTerminado, InventarioRuta, SalidaPTerminado
from VehiculosRutas.forms import VehiculoForm, ClienteDiasVisitaForm,ClienteDiasVisitaFormSet
from .forms import ClienteForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import RutaForm
from django.contrib import messages
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from datetime import date, timedelta
from django.db.models import Q, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from urllib.parse import urlencode


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


from django.urls import reverse

@login_required
def agregar_cliente(request):
    """
    Permite agregar un cliente con varios días de visita.
    Valida los órdenes según la ruta seleccionada.
    """
    cliente = Cliente()

    if request.method == 'POST':
        form = ClienteForm(
            request.POST,
            request.FILES,
            instance=cliente
        )

        dias_formset = ClienteDiasVisitaFormSet(
            request.POST,
            instance=cliente
        )

        # Primero validar los datos del cliente
        cliente_valido = form.is_valid()

        if cliente_valido:
            # La ruta debe estar disponible antes de validar el formset
            cliente.ruta = form.cleaned_data.get('ruta')
            cliente.estado = form.cleaned_data.get('estado')

        # Validar días y órdenes de visita
        dias_validos = dias_formset.is_valid()

        if cliente_valido and dias_validos:
            with transaction.atomic():
                cliente = form.save()

                dias_formset.instance = cliente
                dias_formset.save()

            messages.success(request, "Cliente agregado correctamente.")

            url = reverse('listar_clientes')
            filtros = request.GET.urlencode()

            if filtros:
                url += f'?{filtros}'

            return redirect(url)

        messages.error(
            request,
            "No se pudo guardar el cliente. Revisa los datos y órdenes de visita."
        )

    else:
        form = ClienteForm(instance=cliente)

        dias_formset = ClienteDiasVisitaFormSet(
            instance=cliente
        )

    return render(
        request,
        'VehiculosRutas/clientes/agregar_cliente.html',
        {
            'form': form,
            'dias_formset': dias_formset
        }
    )





@login_required
def editar_cliente(request, pk):
    """
    Permite editar un cliente y sus días de visita.
    Conserva los filtros después de guardar correctamente.
    """
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        form = ClienteForm(
            request.POST,
            request.FILES,
            instance=cliente
        )

        dias_formset = ClienteDiasVisitaFormSet(
            request.POST,
            instance=cliente
        )

        cliente_valido = form.is_valid()

        if cliente_valido:
            cliente.ruta = form.cleaned_data.get('ruta')
            cliente.estado = form.cleaned_data.get('estado')

        dias_validos = dias_formset.is_valid()

        if cliente_valido and dias_validos:
            with transaction.atomic():
                form.save()
                dias_formset.save()

            messages.success(
                request,
                "Cliente actualizado correctamente."
            )

            # Recuperar filtros enviados por el formulario
            ruta = request.POST.get('filtro_ruta', '')
            dia = request.POST.get('filtro_dia', '')
            mostrar_todos = request.POST.get('filtro_mostrar_todos', '')

            params = {}

            if ruta:
                params['ruta'] = ruta

            if dia:
                params['dia'] = dia

            if mostrar_todos == '1':
                params['mostrar_todos'] = '1'

            url = reverse('listar_clientes')

            if params:
                url += '?' + urlencode(params)

            return redirect(url)

        messages.error(
            request,
            "No se pudieron guardar los cambios. Revisa los órdenes de visita."
        )

    else:
        form = ClienteForm(instance=cliente)
        dias_formset = ClienteDiasVisitaFormSet(instance=cliente)

    return render(
        request,
        'VehiculosRutas/clientes/editar_cliente.html',
        {
            'form': form,
            'dias_formset': dias_formset
        }
    )





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

    clientes = Cliente.objects.all() if mostrar_todos else Cliente.objects.filter(estado=True)

    if ruta_id == "sin_ruta":
        clientes = clientes.filter(ruta__isnull=True)
    elif ruta_id and ruta_id != "todas":
        clientes = clientes.filter(ruta__id=ruta_id)

    if dia == "sin_dia":
        clientes = clientes.filter(clientediasvisita__isnull=True)
    elif dia in dict(ClienteDiasVisita.DIAS):
        clientes = clientes.filter(clientediasvisita__dia_semana=dia)

    clientes = clientes.distinct()

    if dia in dict(ClienteDiasVisita.DIAS):
        clientes = ordenar_clientes_por_dia(clientes, dia)
    else:
        clientes = clientes.order_by('nombre', 'id')

    return render(request, 'VehiculosRutas/clientes/listar_clientes.html', {
        'clientes': clientes,
        'rutas': Ruta.objects.all(),
        'dias': ClienteDiasVisita.DIAS,
        'selected_ruta': ruta_id,
        'selected_dia': dia,
        'mostrar_todos': mostrar_todos,
        'semana_actual': inicio_semana_operativa(timezone.localdate()).isoformat()
    })

import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def clientes_data(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '').strip()

    ruta_id = request.GET.get('ruta')
    dia = request.GET.get('dia')
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    qs = Cliente.objects.all()
    if not mostrar_todos:
        qs = qs.filter(estado=True)

    if ruta_id == "sin_ruta":
        qs = qs.filter(ruta__isnull=True)
    elif ruta_id and ruta_id != "todas":
        qs = qs.filter(ruta__id=ruta_id)

    if dia == "sin_dia":
        qs = qs.filter(clientediasvisita__isnull=True)
    elif dia in dict(ClienteDiasVisita.DIAS):
        qs = qs.filter(clientediasvisita__dia_semana=dia)

    if search_value:
        qs = qs.filter(
            Q(nombre__icontains=search_value) |
            Q(nombre_negocio__icontains=search_value) |
            Q(direccion__icontains=search_value) |
            Q(telefono__icontains=search_value)
        )

    qs = qs.distinct()
    total_records = qs.count()

    if dia in dict(ClienteDiasVisita.DIAS):
        qs = ordenar_clientes_por_dia(qs, dia)
    else:
        qs = qs.order_by('nombre', 'id')

    if length != -1:
        qs = qs[start:start + length]

    qs = qs.select_related('ruta').prefetch_related('clientediasvisita_set')

    data = []
    for cliente in qs:
        visitas = sorted(cliente.clientediasvisita_set.all(), key=lambda v: v.orden)

        lista_dias = ", ".join(
            f"{v.get_dia_semana_display()} (Orden {v.orden}, {'Semanal' if v.frecuencia_semanas == 1 else 'Quincenal'})"
            for v in visitas
        ) if visitas else "No asignados"

        acciones_html = render_to_string(
            'VehiculosRutas/clientes/_acciones.html',
            {'cliente': cliente}, request=request
        )

        data.append({
            'nombre': cliente.nombre,
            'nombre_negocio': cliente.nombre_negocio,
            'direccion': cliente.direccion,
            'telefono': cliente.telefono,
            'ruta': cliente.ruta.nombre if cliente.ruta else '',
            'dias_visita': lista_dias,
            'estado': '<span class="badge bg-custom-success">Activo</span>' if cliente.estado
                      else '<span class="badge bg-custom-danger">Inactivo</span>',
            'acciones': acciones_html,
        })

    return JsonResponse({
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data
    })


@login_required
def descargar_clientes_pdf(request):
    ruta = request.GET.get('ruta')
    dia = request.GET.get('dia')
    semana_param = request.GET.get('semana')
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    ruta = ruta if ruta not in [None, '', 'None'] else None
    dia = dia if dia not in [None, '', 'None'] else None

    try:
        fecha = date.fromisoformat(semana_param) if semana_param else timezone.localdate()
    except ValueError:
        return HttpResponse('Semana inválida', status=400)

    semana = inicio_semana_operativa(fecha)
    fin_semana = semana + timedelta(days=6)

    clientes = Cliente.objects.all() if mostrar_todos else Cliente.objects.filter(estado=True)
    nombre_ruta = "Todas"

    if ruta == "sin_ruta":
        clientes = clientes.filter(ruta__isnull=True)
        nombre_ruta = "Sin Ruta"
    elif ruta and ruta != "todas":
        try:
            ruta_obj = Ruta.objects.filter(id=int(ruta)).first()
            clientes = clientes.filter(ruta__id=int(ruta))
            if ruta_obj:
                nombre_ruta = ruta_obj.nombre
        except ValueError:
            return HttpResponse('ID de ruta inválido', status=400)

    if dia == "sin_dia":
        clientes = clientes.filter(clientediasvisita__isnull=True)
        nombre_dia = "Sin día"
        clientes = clientes.order_by('nombre')

    elif dia in dict(ClienteDiasVisita.DIAS):
        clientes = clientes.filter(clientediasvisita__dia_semana=dia)
        nombre_dia = dict(ClienteDiasVisita.DIAS)[dia]

        visitas = ClienteDiasVisita.objects.filter(
            cliente__in=clientes, dia_semana=dia
        ).select_related('cliente')

        ids_clientes = [
            visita.cliente_id for visita in visitas
            if corresponde_visita(visita, semana)
        ]

        clientes = ordenar_clientes_por_dia(
            clientes.filter(id__in=ids_clientes).distinct(), dia
        )

    else:
        nombre_dia = "Todos"
        clientes = clientes.distinct().order_by('nombre')

    context = {
        'mostrar_todos': mostrar_todos,
        'clientes': clientes,
        'ruta': nombre_ruta,
        'dia': nombre_dia,
        'semana_inicio': semana,
        'semana_fin': fin_semana,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="clientes.pdf"'

    template = get_template('VehiculosRutas/clientes/pdf_clientes.html')
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Ocurrió un error al generar el PDF', status=500)

    return response

def inicio_semana_operativa(fecha):
    return fecha - timedelta(days=(fecha.weekday() - 2) % 7)


def corresponde_visita(visita, semana):
    if visita.frecuencia_semanas == 1:
        return True

    if visita.frecuencia_semanas == 2 and visita.semana_referencia:
        referencia = inicio_semana_operativa(visita.semana_referencia)
        diferencia = (semana - referencia).days // 7
        return diferencia % 2 == 0

    return False


def ordenar_clientes_por_dia(qs, dia):
    orden_visita = ClienteDiasVisita.objects.filter(
        cliente_id=OuterRef('pk'), dia_semana=dia
    ).values('orden')[:1]

    return qs.annotate(
        orden_visita=Coalesce(Subquery(orden_visita, output_field=IntegerField()), 999999)
    ).order_by('orden_visita', 'nombre', 'id')


