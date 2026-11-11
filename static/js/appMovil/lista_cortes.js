
document.addEventListener('DOMContentLoaded', () => {
    const contenedor = document.getElementById('listaCortesMinibodega');
    if (!contenedor) return;

    // =========================================================
    // DATATABLES - LISTA DE CORTES
    // =========================================================
    $('#cortesTable').DataTable({
        pageLength: 25,
        responsive: true,
        ordering: true,
        order: [],
        columnDefs: [
            {width: "5%", targets: 0},
            {width: "10%", targets: 1},
            {width: "20%", targets: 2},
            {width: "15%", targets: 3},
            {width: "20%", targets: 4},
            {width: "15%", targets: 5, className: "text-center"},
            {width: "15%", targets: 6, className: "text-center", orderable: false}
        ],
        language: {
            decimal: "",
            emptyTable: "No hay datos disponibles",
            info: "Mostrando _START_ a _END_ de _TOTAL_ cortes",
            infoEmpty: "Mostrando 0 a 0 de 0 cortes",
            infoFiltered: "(filtrado de _MAX_ cortes totales)",
            lengthMenu: "Mostrar _MENU_ cortes",
            loadingRecords: "Cargando...",
            processing: "Procesando...",
            search: "Buscar:",
            zeroRecords: "No se encontraron cortes",
            paginate: {
                first: '<i class="bi bi-rewind-fill"></i>',
                last: '<i class="bi bi-fast-forward-fill"></i>',
                next: '<i class="bi bi-caret-right-fill"></i>',
                previous: '<i class="bi bi-caret-left-fill"></i>'
            }
        }
    });
});
