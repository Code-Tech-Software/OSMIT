
document.addEventListener('DOMContentLoaded', function () {
    const dashboard = document.getElementById('dashboard-produccion');
    if (!dashboard) return;

    const pedidosUrl = dashboard.dataset.pedidosUrl;
    const indicadoresUrl = dashboard.dataset.indicadoresUrl;
    const contenedor = dashboard.querySelector('#lista-pedidos');
    const loading = dashboard.querySelector('#loading');
    let pedidosActuales = [];

    function getEstadoClass(estado) {
        const estados = {
            'Pendiente': 'bg-warning text-dark',
            'Completado': 'bg-success',
            'Rechazado': 'bg-danger',
            'Finalizado': 'bg-info'
        };
        return estados[estado] || 'bg-success';
    }

    function crearElemento(etiqueta, clase, texto) {
        const elemento = document.createElement(etiqueta);
        if (clase) elemento.className = clase;
        if (texto !== undefined && texto !== null) elemento.textContent = texto;
        return elemento;
    }

    async function cargarPedidos() {
        try {
            const resp = await fetch(pedidosUrl);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const pedidos = await resp.json();
            if (!Array.isArray(pedidos)) throw new Error('Formato de pedidos inválido');

            pedidosActuales = pedidos;
            contenedor.replaceChildren();

            pedidos.forEach((pedido, index) => {
                const col = crearElemento('div', 'col');
                const card = crearElemento('div', 'card pedido-card h-100 shadow-sm');
                const body = crearElemento('div', 'card-body');
                const titulo = crearElemento('h5', 'card-title', `Pedido #${pedido.id}`);
                const fecha = crearElemento('p', 'card-text');
                const fechaTexto = crearElemento('small', 'text-muted', pedido.fecha);
                const usuario = crearElemento('p', 'card-text');
                const usuarioNombre = crearElemento('strong', '', pedido.usuario);
                const estado = crearElemento('span', `badge ${getEstadoClass(pedido.estado)}`, pedido.estado);
                const footer = crearElemento('div', 'card-footer');
                const boton = crearElemento('button', 'btn btn-detalle btn-sm w-100', 'Ver Detalle');

                boton.type = 'button';
                boton.addEventListener('click', () => verDetalle(pedidosActuales[index]));
                fecha.appendChild(fechaTexto);
                usuario.append('Usuario: ', usuarioNombre);
                body.append(titulo, fecha, usuario, estado);
                footer.appendChild(boton);
                card.append(body, footer);
                col.appendChild(card);
                contenedor.appendChild(col);
            });

            loading.classList.add('d-none');
            contenedor.classList.remove('d-none');
        } catch (error) {
            console.error('Error al cargar pedidos:', error);
            loading.innerHTML = '<div class="alert alert-danger">Error al cargar los pedidos. Intente recargar la página.</div>';
        }
    }

    function verDetalle(pedido) {
        dashboard.querySelector('#modal-fecha').textContent = pedido.fecha;
        dashboard.querySelector('#modal-usuario').textContent = pedido.usuario;
        dashboard.querySelector('#modal-nota').textContent = pedido.nota || '(Sin nota)';

        const estado = dashboard.querySelector('#modal-estado');
        estado.textContent = pedido.estado;
        estado.className = `badge ${getEstadoClass(pedido.estado)}`;

        const productos = dashboard.querySelector('#modal-productos');
        productos.replaceChildren();

        (pedido.detalles || []).forEach(detalle => {
            const li = crearElemento('li', 'list-group-item d-flex justify-content-between align-items-center');
            const info = crearElemento('div');
            const nombre = crearElemento('strong', '', detalle.producto);
            const cantidad = crearElemento('small', 'text-muted', `${detalle.cantidad} ${detalle.unidad}`);
            const usuario = crearElemento('small', 'text-muted', detalle.usuario);

            info.append(nombre, document.createElement('br'), cantidad);
            li.append(info, usuario);
            productos.appendChild(li);
        });

        bootstrap.Modal.getOrCreateInstance(dashboard.querySelector('#detalleModal')).show();
    }

    async function cargarIndicadores() {
        try {
            const resp = await fetch(indicadoresUrl);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            dashboard.querySelector('#productos_bajo_min').textContent = data.productos_bajo_min;
            dashboard.querySelector('#productos_sin_stock').textContent = data.productos_sin_stock;
            dashboard.querySelector('#pedidos_pendientes').textContent = data.pedidos_pendientes;
            dashboard.querySelector('#pedidos_en_produccion').textContent = data.pedidos_en_produccion;
        } catch (error) {
            console.error('Error cargando indicadores de Producción:', error);
        }
    }

    cargarPedidos();
    cargarIndicadores();
});
