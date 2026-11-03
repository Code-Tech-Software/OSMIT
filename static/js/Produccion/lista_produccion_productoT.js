
$(document).ready(function () {
    // Tabla de productos terminados
    $('#terminadosTable').DataTable({
        pageLength: 25,
        responsive: true,
        order: [],
        language: {
            decimal: "",
            emptyTable: "No hay productos registrados",
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

    // Botón refrescar
    $('#refreshBtn').on('click', function () {
        $('#refreshIcon').addClass('d-none');
        $('#refreshSpinner').removeClass('d-none');
        setTimeout(function () {
            location.reload();
        }, 200);
    });
});
