
$(document).ready(function () {
    $('#productosTable').DataTable({
        pageLength: 10,
        autoWidth: false,
        responsive: true,
        columnDefs: [
            {width: "24%", targets: 0},
            {width: "55%", targets: 1},
            {width: "10%", targets: 2, className: "text-center"},
            {width: "11%", targets: 3, className: "text-center"}
        ],
        language: {
            decimal: "",
            emptyTable: "No hay datos disponibles",
            info: "Mostrando _START_ a _END_ de _TOTAL_ productos",
            infoEmpty: "Mostrando 0 a 0 de 0 productos",
            infoFiltered: "(filtrado de _MAX_ productos totales)",
            lengthMenu: "Mostrar _MENU_ productos",
            loadingRecords: "Cargando...",
            processing: "Procesando...",
            search: "Buscar:",
            zeroRecords: "No se encontraron productos",
            paginate: {
                first: '<i class="bi bi-rewind-fill"></i>',
                last: '<i class="bi bi-fast-forward-fill"></i>',
                next: '<i class="bi bi-caret-right-fill"></i>',
                previous: '<i class="bi bi-caret-left-fill"></i>'
            }
        }
    });

    $('#toggleEstado').on('change', function () {
        const url = new URL(window.location.href);
        if (this.checked) url.searchParams.set('mostrar_todos', '1');
        else url.searchParams.delete('mostrar_todos');
        window.location.href = url.toString();
    });

    $('#productosTable').on('click', '.btn-delete', function (e) {
        e.preventDefault();
        const url = $(this).attr('href');

        Swal.fire({
            title: '¿Estás seguro?',
            text: '¡Esta acción desactivará el producto!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: 'var(--danger-color)',
            cancelButtonColor: 'var(--secondary-color)',
            confirmButtonText: 'Sí, desactivar',
            cancelButtonText: 'Cancelar'
        }).then(result => {
            if (result.isConfirmed) window.location.href = url;
        });
    });
});
