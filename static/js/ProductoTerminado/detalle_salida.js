
$(document).ready(function () {
    const detalleSalida = document.getElementById('detalleSalidaPT');
    if (!detalleSalida) return;

    const obtenerElemento = id => document.getElementById(id);

    // =========================================================
    // DATATABLES - PRODUCTOS
    // =========================================================
    const idiomaProductos = {
        emptyTable: 'No hay productos registrados',
        zeroRecords: 'No se encontraron productos',
        info: 'Mostrando _START_ a _END_ de _TOTAL_ productos',
        infoEmpty: 'Mostrando 0 a 0 de 0 productos',
        lengthMenu: 'Mostrar _MENU_ productos',
        search: 'Buscar:',
        paginate: {first:'Primero', last:'Último', next:'Siguiente', previous:'Anterior'}
    };

    $('#detalleSalidaTable').DataTable({
        pageLength: 25,
        responsive: true,
        order: [],
        language: idiomaProductos
    });

    // =========================================================
    // DATATABLES - HISTORIAL DE CORRECCIONES
    // =========================================================
    if ($('#correccionesTable').length) {
        $('#correccionesTable').DataTable({
            pageLength: 10,
            responsive: true,
            order: [[0,'asc']],
            language: {
                emptyTable: 'No hay correcciones registradas',
                zeroRecords: 'No se encontraron correcciones',
                info: 'Mostrando _START_ a _END_ de _TOTAL_ correcciones',
                infoEmpty: 'Mostrando 0 a 0 de 0 correcciones',
                lengthMenu: 'Mostrar _MENU_ correcciones',
                search: 'Buscar:',
                paginate: {first:'Primero', last:'Último', next:'Siguiente', previous:'Anterior'}
            }
        });
    }

    // =========================================================
    // MODAL DE CORRECCIONES
    // =========================================================
    const modalCorreccion = obtenerElemento('modalCorreccion');
    if (!modalCorreccion) return;

    const opciones = obtenerElemento('opcionesCorreccion');
    const productoContainer = obtenerElemento('correccionProductoContainer');
    const cantidadContainer = obtenerElemento('correccionCantidadContainer');
    const eliminarContainer = obtenerElemento('eliminarProductoContainer');
    const cantidadInput = obtenerElemento('cantidadNuevaInput');

    let detalleIdActual = null;
    let cantidadActual = null;
    let precioActual = null;

    function mostrarOpcionesCorreccion() {
        opciones.classList.remove('d-none');
        productoContainer.classList.add('d-none');
        cantidadContainer.classList.add('d-none');
        eliminarContainer.classList.add('d-none');
    }

    function mostrarSeccion(seccion) {
        mostrarOpcionesCorreccion();
        opciones.classList.add('d-none');
        seccion.classList.remove('d-none');
    }

    // =========================================================
    // BOTONES DE CORRECCIÓN
    // =========================================================
    obtenerElemento('btnCorregirProducto').addEventListener('click', () => {
        mostrarSeccion(productoContainer);
    });

    obtenerElemento('btnCorregirCantidad').addEventListener('click', () => {
        mostrarSeccion(cantidadContainer);
        cantidadInput.value = cantidadActual;
    });

    obtenerElemento('btnEliminarProducto').addEventListener('click', () => {
        mostrarSeccion(eliminarContainer);
    });

    // BOTONES REGRESAR
    obtenerElemento('btnVolverCorrecciones').addEventListener('click', mostrarOpcionesCorreccion);
    obtenerElemento('btnVolverCantidad').addEventListener('click', mostrarOpcionesCorreccion);
    obtenerElemento('btnVolverEliminar').addEventListener('click', mostrarOpcionesCorreccion);

    // =========================================================
    // ABRIR MODAL Y CARGAR INFORMACIÓN
    // =========================================================
    modalCorreccion.addEventListener('show.bs.modal', function(event) {
        const boton = event.relatedTarget;
        if (!boton) return;

        detalleIdActual = boton.dataset.detalleId;
        cantidadActual = boton.dataset.cantidad;
        precioActual = boton.dataset.precio;

        obtenerElemento('correccionProducto').textContent = boton.dataset.producto;
        obtenerElemento('correccionPresentacion').textContent = boton.dataset.presentacion;
        obtenerElemento('correccionCantidad').textContent = cantidadActual;
        obtenerElemento('correccionPrecio').textContent = precioActual
            ? '$' + parseFloat(precioActual).toFixed(2)
            : '-';

        mostrarOpcionesCorreccion();
        obtenerElemento('productoNuevoSelect').value = '';
        cantidadInput.value = cantidadActual;
    });

    // =========================================================
    // EVITAR CAMBIOS ACCIDENTALES DE CANTIDAD
    // =========================================================
    cantidadInput.addEventListener('wheel', function(event) {
        if (document.activeElement === this) {
            event.preventDefault();
            this.blur();
        }
    }, {passive:false});

    cantidadInput.addEventListener('keydown', function(event) {
        if (['ArrowUp','ArrowDown'].includes(event.key)) {
            event.preventDefault();
        }
    });

    // =========================================================
    // ENVÍO DE FORMULARIOS DE CORRECCIÓN
    // =========================================================
    function configurarFormulario(id) {
        const formulario = obtenerElemento(id);
        if (!formulario) return;

        formulario.addEventListener('submit', function(event) {
            event.preventDefault();

            if (!detalleIdActual) {
                alert('No se pudo identificar el producto a corregir.');
                return;
            }

            const urlBase = detalleSalida.dataset.urlCorregir;
            if (!urlBase) {
                console.error('No se encontró la URL de corrección.');
                alert('No se pudo obtener la dirección para corregir el producto.');
                return;
            }

            this.action = urlBase.replace(
                /\/0(?=\/|$)/,
                `/${encodeURIComponent(detalleIdActual)}`
            );

            this.submit();
        });
    }

    configurarFormulario('formCorreccionProducto');
    configurarFormulario('formCorreccionCantidad');
    configurarFormulario('formEliminarProducto');
});
