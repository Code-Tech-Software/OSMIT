
$(document).ready(function () {
    window.productosDT = $('#productosTable').DataTable({
        pageLength: 50,
        responsive: true,
        columnDefs: [
            {width: "30%", targets: 0},
            {width: "20%", targets: 1},
            {width: "20%", targets: 2},
            {width: "30%", targets: 3}
        ],
        language: {
            decimal: "",
            emptyTable: "No hay productos disponibles",
            info: "Mostrando _START_ a _END_ de _TOTAL_ productos",
            infoEmpty: "Mostrando 0 a 0 de 0 productos",
            infoFiltered: "(filtrado de _MAX_ productos en total)",
            lengthMenu: "Mostrar _MENU_ productos",
            loadingRecords: "Cargando...",
            processing: "Procesando...",
            search: "Buscar:",
            zeroRecords: "No se encontraron productos coincidentes",
            paginate: {
                first: '<i class="bi bi-rewind-fill"></i>',
                last: '<i class="bi bi-fast-forward-fill"></i>',
                next: '<i class="bi bi-caret-right-fill"></i>',
                previous: '<i class="bi bi-caret-left-fill"></i>'
            }
        }
    });
});

const form = document.getElementById('entradaGranelForm');
const submitBtn = document.getElementById('submitBtn');
const confirmSubmit = document.getElementById('confirmSubmit');
const resumenEntrada = document.getElementById('resumenEntrada');
const confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));
const notyf = new Notyf({
    duration: 2500,
    position: {x: 'right', y: 'bottom'},
    dismissible: true
});

function escaparHTML(valor) {
    const div = document.createElement('div');
    div.textContent = String(valor);
    return div.innerHTML;
}

function obtenerFechaLocal() {
    const fecha = new Date();
    const anio = fecha.getFullYear();
    const mes = String(fecha.getMonth() + 1).padStart(2, '0');
    const dia = String(fecha.getDate()).padStart(2, '0');
    return `${anio}-${mes}-${dia}`;
}

// Activar o desactivar fecha manual, incluso en páginas de DataTables.
$('#productosTable').on('change', '.caducidad-manual', function () {
    const celda = this.closest('td');
    const fecha = celda.querySelector('.fecha-caducidad');
    const texto = celda.querySelector('.texto-caducidad');

    fecha.disabled = !this.checked;
    fecha.required = this.checked;
    if (!this.checked) fecha.value = '';

    texto.textContent = this.checked ? 'Caducidad personalizada' : 'Automática';
});

// Interceptar envío y mostrar modal de confirmación.
form.addEventListener('submit', function (e) {
    e.preventDefault();

    const dt = window.productosDT;
    const rows = [];
    const hoy = obtenerFechaLocal();
    let error = false;

    dt.$('input[name^="cantidad_"]').each(function () {
        const cantidad = Number(this.value);
        if (!Number.isFinite(cantidad) || cantidad <= 0) return;

        const tr = this.closest('tr');
        const tds = tr.children;
        const nombre = tds[0]?.textContent.trim() || '';
        const stock = tds[1]?.textContent.trim() || '';
        const fecha = tr.querySelector('.fecha-caducidad');
        const manual = tr.querySelector('.caducidad-manual')?.checked || false;

        if (manual && (!fecha.value || fecha.value < hoy)) {
            notyf.error(`Revisa la fecha de caducidad de ${nombre}.`);
            error = true;
            return;
        }

        const caducidad = manual ? fecha.value : 'Automática';

        rows.push(`
            <tr>
                <td>${escaparHTML(nombre)}</td>
                <td>${escaparHTML(stock)}</td>
                <td>${cantidad}</td>
                <td>${escaparHTML(caducidad)}</td>
            </tr>
        `);
    });

    if (error) return;

    if (rows.length === 0) {
        notyf.error('Debes ingresar al menos una cantidad mayor a 0.');
        return;
    }

    const nota = document.getElementById('nota').value || '(Sin nota)';

    resumenEntrada.innerHTML = `
        <div class="mb-3 p-3 bg-light rounded">
            <p class="mb-0"><strong>Nota:</strong> ${escaparHTML(nota)}</p>
        </div>
        <div class="table-responsive">
            <table class="table table-bordered table-sm">
                <thead class="table-light">
                    <tr>
                        <th>Producto</th>
                        <th>Stock Actual</th>
                        <th>Cantidad a agregar</th>
                        <th>Caducidad</th>
                    </tr>
                </thead>
                <tbody>${rows.join('')}</tbody>
            </table>
        </div>
    `;

    confirmModal.show();
});

// Enviar cantidades y fechas, incluyendo páginas ocultas.
confirmSubmit.addEventListener('click', function () {
    const dt = window.productosDT;

    confirmSubmit.disabled = true;
    confirmSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Registrando Entrada...';
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Registrando...';

    dt.$('input[name^="cantidad_"], input[name^="fecha_caducidad_"]').each(function () {
        if (!document.contains(this) && !this.disabled && this.value !== '') {
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = this.name;
            hidden.value = this.value;
            form.appendChild(hidden);
        }
    });

    form.submit();
});

// Evitar envío accidental con Enter.
form.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.tagName.toLowerCase() !== 'textarea') {
        e.preventDefault();
    }
});

// Evitar modificar cantidades con la rueda del mouse
document.querySelector('#productosTable').addEventListener('wheel', function (e) {
    if (e.target.classList.contains('cantidad-entrada')) {
        e.target.blur();
    }
}, {passive: true});