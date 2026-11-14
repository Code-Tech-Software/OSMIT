
$(document).ready(function () {
    $('#tablaEntradas').DataTable({
        pageLength: 25,
        lengthMenu: [10, 25, 50, 100],
        ordering: true,
        order: [],
        autoWidth: false,
        columnDefs: [
            { targets: 0, width: '7%' },
            { targets: 1, width: '20%' },
            { targets: 2, width: '18%' },
            { targets: 3, width: '35%' },
            { targets: 4, width: '20%', orderable: false }
        ],
        language: {
            decimal: ",",
            thousands: ".",
            lengthMenu: "Mostrar _MENU_ registros",
            zeroRecords: "No se encontraron entradas",
            info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
            infoEmpty: "No hay entradas registradas",
            infoFiltered: "(filtrado de _MAX_ entradas)",
            search: "Buscar:",
            emptyTable: "No hay entradas registradas para esta fecha.",
            paginate: {
                first: '<i class="bi bi-chevron-double-left"></i>',
                previous: '<i class="bi bi-chevron-left"></i>',
                next: '<i class="bi bi-chevron-right"></i>',
                last: '<i class="bi bi-chevron-double-right"></i>'
            }
        }
    });

    const contenedor = document.getElementById('historialEntradas');
    const input = document.getElementById('fechaEntrada');
    const urlFechas = contenedor.dataset.urlFechas;
    const cacheFechas = new Map();
    let fechasMarcadas = {};

    async function cargarFechas(anio, mes, calendario) {
        const clave = `${anio}-${mes}`;
        if (cacheFechas.has(clave)) {
            fechasMarcadas = cacheFechas.get(clave);
            calendario.redraw();
            return;
        }

        try {
            const parametros = new URLSearchParams({ anio, mes });
            const respuesta = await fetch(`${urlFechas}?${parametros.toString()}`);
            if (!respuesta.ok) throw new Error('Error al consultar fechas');
            const datos = await respuesta.json();
            fechasMarcadas = datos.fechas || {};
            cacheFechas.set(clave, fechasMarcadas);
            calendario.redraw();
        } catch (error) {
            console.error('No se pudieron cargar las fechas con entradas:', error);
            fechasMarcadas = {};
            calendario.redraw();
        }
    }

    const calendario = flatpickr(input, {
        locale: 'es',
        dateFormat: 'Y-m-d',
        altInput: true,
        altFormat: 'd/m/Y',
        allowInput: false,
        maxDate: input.dataset.maxFecha,
        disableMobile: true,
        onReady: function (_, __, instancia) {
            cargarFechas(instancia.currentYear, instancia.currentMonth + 1, instancia);
        },
        onMonthChange: function (_, __, instancia) {
            cargarFechas(instancia.currentYear, instancia.currentMonth + 1, instancia);
        },
        onYearChange: function (_, __, instancia) {
            cargarFechas(instancia.currentYear, instancia.currentMonth + 1, instancia);
        },
        onDayCreate: function (_, __, instancia, elementoDia) {
            const fecha = elementoDia.dateObj;
            const anio = fecha.getFullYear();
            const mes = String(fecha.getMonth() + 1).padStart(2, '0');
            const dia = String(fecha.getDate()).padStart(2, '0');
            const clave = `${anio}-${mes}-${dia}`;
            const total = fechasMarcadas[clave];

            if (total) {
                elementoDia.classList.add('tiene-entrada');
                elementoDia.title = `${total} entrada${total === 1 ? '' : 's'} registrada${total === 1 ? '' : 's'}`;
            }
        }
    });
});
