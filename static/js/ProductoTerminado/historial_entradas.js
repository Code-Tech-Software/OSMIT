
$(document).ready(function () {
    const tabla = document.getElementById('entradasTable');
    if (!tabla) return;

    $('#entradasTable').DataTable({
        pageLength: 25,
        responsive: true,
        order: [[1,'desc']],
        language: {
            emptyTable: 'No hay entradas registradas',
            zeroRecords: 'No se encontraron entradas',
            info: 'Mostrando _START_ a _END_ de _TOTAL_ entradas',
            infoEmpty: 'Mostrando 0 a 0 de 0 entradas',
            lengthMenu: 'Mostrar _MENU_ entradas',
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
