
$(document).ready(function () {
    $('#salidasTable').DataTable({
        pageLength: 10,
        autoWidth: false,
        responsive: true,
        order: [[0, 'desc']],
        columnDefs: [
            {width: "5%", targets: 0},
            {width: "20%", targets: 1},
            {width: "12%", targets: 2},
            {width: "12%", targets: 3},
            {width: "25%", targets: 4},
            {width: "26%", targets: 5, className: "text-center"}
        ],
        language: {
            emptyTable: "No hay salidas registradas en esta fecha",
            info: "Mostrando _START_ a _END_ de _TOTAL_ salidas",
            infoEmpty: "Mostrando 0 a 0 de 0 salidas",
            infoFiltered: "(filtrado de _MAX_ salidas en total)",
            lengthMenu: "Mostrar _MENU_ salidas",
            loadingRecords: "Cargando...",
            processing: "Procesando...",
            search: "Buscar:",
            zeroRecords: "No se encontraron coincidencias",
            paginate: {
                first: '<i class="bi bi-rewind-fill"></i>',
                last: '<i class="bi bi-fast-forward-fill"></i>',
                next: '<i class="bi bi-caret-right-fill"></i>',
                previous: '<i class="bi bi-caret-left-fill"></i>'
            }
        }
    });
});
