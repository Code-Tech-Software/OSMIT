
// SWITCH ORIGINAL: MOSTRAR PRODUCTOS INACTIVOS
$('#toggleEstado').on('change', function () {
    const url = new URL(window.location.href);
    if ($(this).is(':checked')) {
        url.searchParams.set('mostrar_todos', '1');
    } else {
        url.searchParams.delete('mostrar_todos');
    }
    window.location.href = url.toString();
});

// SWITCH ORIGINAL: ORDEN DE RUTA
$('#ordenPersonalizado').on('change', function () {
    const url = new URL(window.location.href);
    if ($(this).is(':checked')) {
        url.searchParams.set('orden', 'personalizado');
    } else {
        url.searchParams.delete('orden');
    }
    window.location.href = url.toString();
});

$(document).ready(function () {
    const contenedor = document.getElementById('listarProductosPT');
    if (!contenedor) return;

    const esAdmin = contenedor.dataset.admin === 'true';
    const columnas = [
        {width: "20%", targets: 0},
        {width: "55%", targets: 1, orderable: false},
        {width: "10%", targets: 2, className: "text-center"}
    ];
    if (esAdmin) {
        columnas.push({width: "15%", targets: 3, className: "text-center", orderable: false});
    }

    $('#productosPTTable').DataTable({
        pageLength: 50,
        order: [],
        columnDefs: columnas,
        language: {
            decimal: "",
            emptyTable: "No hay productos disponibles",
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
        },
        responsive: true
    });

    // CONFIRMACIÓN ORIGINAL PARA ELIMINAR
    $('.btn-delete').on('click', function (e) {
        e.preventDefault();
        const url = $(this).attr('href');
        Swal.fire({
            title: '¿Estás seguro?',
            text: "¡Esta acción eliminará el producto y TODAS sus variaciones!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: 'var(--danger-color)',
            cancelButtonColor: 'var(--secondary-color)',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) window.location.href = url;
        });
    });

    // NOTIFICACIONES ORIGINALES
    const notyf = new Notyf({
        duration: 3000,
        position: {x:'right', y:'bottom'},
        dismissible: true
    });

    document.querySelectorAll('#mensajesProductosPT [data-tipo]').forEach(function (mensaje) {
        const tipos = mensaje.dataset.tipo.split(' ');
        const texto = mensaje.dataset.texto;
        if (tipos.includes('success')) notyf.success(texto);
        else if (tipos.includes('error')) notyf.error(texto);
    });
});
