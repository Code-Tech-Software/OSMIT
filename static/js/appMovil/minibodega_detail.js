
document.addEventListener('DOMContentLoaded', () => {
    const contenedor = document.getElementById('minibodegaDetail');
    if (!contenedor) return;

    const bodegaId = contenedor.dataset.bodegaId;
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value
        || document.cookie.split('; ').find(c => c.startsWith('csrftoken='))?.split('=')[1];

    // =========================================================
    // DATATABLES
    // =========================================================
    if (typeof $ !== 'undefined' && $.fn.DataTable) {
        $('#detalleTable').DataTable({
            pageLength: 25,
            responsive: true,
            ordering: true,
            order: [],
            columnDefs: [
                { width: "35%", targets: 0 },
                { width: "15%", targets: 1 },
                { width: "15%", targets: 2 },
                { width: "20%", targets: 3 },
                { width: "15%", targets: 4, orderable: false }
            ],
            language: {
                decimal: "",
                emptyTable: "No hay productos registrados en esta mini bodega.",
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
    }

    // =========================================================
    // ACTIVAR MINIBODEGA MANUALMENTE
    // =========================================================
    document.getElementById('btnActivarMinibodega')?.addEventListener('click', () => {
        Swal.fire({
            title: 'Activar Mini Bodega',
            html: '<p class="text-muted small mb-3">Al activar esta bodega, su estado cambiará a <b>Abierta</b>. Esto permitirá que la ruta vuelva a operar y se puedan registrar nuevos movimientos.</p>Para habilitar esta bodega manualmente, escribe la palabra <b>aceptar</b>.',
            input: 'text',
            inputPlaceholder: 'Escribe aceptar aquí...',
            showCancelButton: true,
            confirmButtonColor: '#198754',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, Activar',
            cancelButtonText: 'Cancelar',
            inputValidator: value => {
                if (!value || value.toLowerCase().trim() !== 'aceptar') {
                    return 'Debes escribir la palabra "aceptar" para continuar.';
                }
            }
        }).then(result => {
            if (!result.isConfirmed) return;

            fetch(`/movil/minibodega/${bodegaId}/abrir/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire('¡Abierta!', data.message, 'success').then(() => location.reload());
                    } else {
                        Swal.fire('Error', data.message, 'error');
                    }
                })
                .catch(() => Swal.fire('Error', 'Ocurrió un error en el servidor.', 'error'));
        });
    });

    // =========================================================
    // REGRESAR PRODUCTO AL INVENTARIO PRINCIPAL
    // =========================================================
    document.getElementById('detalleTable')?.addEventListener('click', event => {
        const boton = event.target.closest('.btn-regresar-producto');
        if (!boton) return;

        const detalleId = boton.dataset.detalleId;
        const productoNombre = boton.dataset.producto;
        const maxCantidad = parseFloat(boton.dataset.cantidad);

        Swal.fire({
            title: 'Regresar a Inventario',
            html: `<p class="text-muted small mb-3">Esta acción sacará la mercancía de la ruta y la <b>sumará de regreso al inventario de la bodega principal</b>, generando un registro de entrada automático.</p>
                   ¿Cuánto deseas devolver de <b id="nombreProductoRegreso"></b>?<br><br>
                   <span class="text-muted">Cantidad actual disponible en la ruta: ${maxCantidad}</span>`,
            didOpen: () => {
                document.getElementById('nombreProductoRegreso').textContent = productoNombre;
            },
            input: 'number',
            inputValue: maxCantidad,
            inputAttributes: { min: 0.1, max: maxCantidad, step: 'any' },
            showCancelButton: true,
            confirmButtonColor: '#ffc107',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Regresar Stock',
            cancelButtonText: 'Cancelar',
            inputValidator: value => {
                const cantidad = parseFloat(value);
                if (!value || isNaN(cantidad) || cantidad <= 0) return 'Ingresa una cantidad mayor a 0.';
                if (cantidad > maxCantidad) return `No puedes regresar más de ${maxCantidad}.`;
            }
        }).then(result => {
            if (!result.isConfirmed) return;

            fetch(`/movil/minibodega/detalle/${detalleId}/regresar/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
                body: JSON.stringify({ cantidad: parseFloat(result.value) })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire('¡Devuelto!', data.message, 'success').then(() => location.reload());
                    } else {
                        Swal.fire('Error', data.message, 'error');
                    }
                })
                .catch(() => Swal.fire('Error', 'No se pudo comunicar con el servidor.', 'error'));
        });
    });
});

