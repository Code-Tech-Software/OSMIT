
$(document).ready(function () {
    if (!document.getElementById('salidasTable')) return;

    $('#salidasTable').DataTable({
        pageLength: 25,
        responsive: true,
        order: [[1, 'desc']],
        language: {
            emptyTable: 'No hay salidas registradas',
            zeroRecords: 'No se encontraron salidas',
            info: 'Mostrando _START_ a _END_ de _TOTAL_ salidas',
            infoEmpty: 'Mostrando 0 a 0 de 0 salidas',
            lengthMenu: 'Mostrar _MENU_ salidas',
            search: 'Buscar:',
            paginate: {
                first: 'Primero',
                last: 'Último',
                next: 'Siguiente',
                previous: 'Anterior'
            }
        }
    });
});
