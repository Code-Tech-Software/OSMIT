
document.addEventListener('DOMContentLoaded', function () {
    const dashboard = document.getElementById('dashboard-recursos-humanos');
    if (!dashboard) return;

    const stockUrl = dashboard.dataset.stockUrl;
    const bajoBody = dashboard.querySelector('#bajo-stock-body');
    const sinBody = dashboard.querySelector('#sin-stock-body');

    function crearElemento(tag, clase = '', texto = null) {
        const elemento = document.createElement(tag);
        if (clase) elemento.className = clase;
        if (texto !== null && texto !== undefined) elemento.textContent = texto;
        return elemento;
    }

    function mostrarMensaje(body, mensaje, clase = 'text-muted', columnas = 3) {
        const tr = crearElemento('tr');
        const td = crearElemento('td', `text-center py-3 ${clase}`, mensaje);
        td.colSpan = columnas;
        tr.appendChild(td);
        body.replaceChildren(tr);
    }

    function mostrarCarga(body, columnas, color) {
        const tr = crearElemento('tr');
        const td = crearElemento('td', 'text-center py-3');
        const spinner = crearElemento('div', `spinner-border spinner-border-sm text-${color}`);
        spinner.setAttribute('role', 'status');
        spinner.appendChild(crearElemento('span', 'visually-hidden', 'Cargando...'));
        td.colSpan = columnas;
        td.appendChild(spinner);
        tr.appendChild(td);
        body.replaceChildren(tr);
    }

    function crearContacto(producto) {
        const td = crearElemento('td');
        if (producto.telefono) {
            const telefono = String(producto.telefono);
            const enlace = crearElemento('a', 'text-decoration-none d-block', telefono);
            enlace.href = `tel:${telefono.replace(/[^\d+]/g, '')}`;
            enlace.prepend(crearElemento('i', 'bi bi-telephone text-primary me-1'));
            td.appendChild(enlace);
        }
        if (producto.correo) {
            const correo = String(producto.correo);
            const enlace = crearElemento('a', 'text-decoration-none d-block', 'Email');
            enlace.href = `mailto:${correo}`;
            enlace.prepend(crearElemento('i', 'bi bi-envelope text-primary me-1'));
            td.appendChild(enlace);
        }
        return td;
    }

    function crearCeldaProducto(producto) {
        const td = crearElemento('td');
        td.appendChild(crearElemento('div', 'fw-semibold', producto.nombre));
        td.appendChild(crearElemento('small', 'text-muted', producto.categoria));
        return td;
    }

    function renderizarBajoStock(productos) {
        if (!productos.length) {
            mostrarMensaje(bajoBody, 'No hay productos con bajo stock', 'text-muted', 5);
            return;
        }
        const fragmento = document.createDocumentFragment();
        productos.forEach(producto => {
            const tr = crearElemento('tr');
            const stock = crearElemento('td', Number(producto.stock) <= 0 ? 'text-danger fw-bold' : '', producto.stock);
            tr.append(
                crearCeldaProducto(producto),
                stock,
                crearElemento('td', '', producto.stock_min),
                crearElemento('td', '', producto.proveedor),
                crearContacto(producto)
            );
            fragmento.appendChild(tr);
        });
        bajoBody.replaceChildren(fragmento);
    }

    function renderizarSinStock(productos) {
        if (!productos.length) {
            mostrarMensaje(sinBody, 'No hay productos sin stock', 'text-muted', 3);
            return;
        }
        const fragmento = document.createDocumentFragment();
        productos.forEach(producto => {
            const tr = crearElemento('tr');
            tr.append(
                crearCeldaProducto(producto),
                crearElemento('td', '', producto.proveedor),
                crearContacto(producto)
            );
            fragmento.appendChild(tr);
        });
        sinBody.replaceChildren(fragmento);
    }

    async function cargarStock() {
        mostrarCarga(bajoBody, 5, 'warning');
        mostrarCarga(sinBody, 3, 'danger');

        try {
            const res = await fetch(stockUrl);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const bajoStock = data.bajo_stock || [];
            const sinStock = data.sin_stock || [];

            dashboard.querySelector('#low-stock-count').textContent = bajoStock.length;
            dashboard.querySelector('#no-stock-count').textContent = sinStock.length;
            renderizarBajoStock(bajoStock);
            renderizarSinStock(sinStock);
        } catch (error) {
            console.error('Error cargando inventario para Recursos Humanos:', error);
            mostrarMensaje(bajoBody, 'Error al cargar los datos', 'text-danger', 5);
            mostrarMensaje(sinBody, 'Error al cargar los datos', 'text-danger', 3);
        }
    }

    async function cargarIndicadores() {
        try {
            const res = await fetch('/granel/api/indicadores/');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            dashboard.querySelector('#total_productos').textContent = data.total_productos;
            dashboard.querySelector('#productos_bajo_min').textContent = data.productos_bajo_min;
            dashboard.querySelector('#productos_sin_stock').textContent = data.productos_sin_stock;
            dashboard.querySelector('#valor_total_stock').textContent =
                `$${Number(data.valor_total_stock).toFixed(2)}`;
        } catch (error) {
            console.error('Error cargando indicadores de Recursos Humanos:', error);
        }
    }

    cargarStock();
    cargarIndicadores();

    const botonActualizar = dashboard.querySelector('#refresh-btn');
    if (botonActualizar) botonActualizar.addEventListener('click', cargarStock);
});
