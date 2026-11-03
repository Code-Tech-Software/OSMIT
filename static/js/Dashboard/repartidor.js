
document.addEventListener('DOMContentLoaded', function () {
    const dashboard = document.getElementById('dashboard-repartidor');
    if (!dashboard) return;

    const elemento = id => dashboard.querySelector(`#${id}`);
    const poner = (id, valor) => {
        const el = elemento(id);
        if (el) el.textContent = valor ?? '-';
    };
    const dinero = valor => {
        const numero = Number(valor ?? 0);
        return new Intl.NumberFormat('es-MX', {
            style: 'currency', currency: 'MXN'
        }).format(Number.isFinite(numero) ? numero : 0);
    };
    const balance = valor => {
        const numero = Number(valor ?? 0);
        return `${numero > 0 ? '+' : numero < 0 ? '-' : ''}${dinero(Math.abs(numero))}`;
    };

    function mostrarInventario(inventario) {
        const tabla = elemento('tabla_inventario');
        tabla.replaceChildren();
        poner('cantidad_productos_inventario', `${inventario.length} productos`);

        if (!inventario.length) {
            const fila = document.createElement('tr');
            const celda = document.createElement('td');
            celda.colSpan = 4;
            celda.className = 'text-center text-muted py-4';
            celda.textContent = 'No hay productos registrados en la MiniBodega.';
            fila.appendChild(celda);
            tabla.appendChild(fila);
            return;
        }

        const fragmento = document.createDocumentFragment();
        inventario.forEach(detalle => {
            const fila = document.createElement('tr');
            [
                detalle.producto,
                detalle.presentacion,
                detalle.cantidad_inicial,
                detalle.cantidad_actual
            ].forEach((valor, indice) => {
                const celda = document.createElement('td');
                celda.textContent = valor ?? '-';
                if (indice >= 2) celda.className = 'text-end';
                fila.appendChild(celda);
            });
            fragmento.appendChild(fila);
        });
        tabla.appendChild(fragmento);
    }

    function mostrarInformacion(data) {
        poner('nombre_repartidor', data.repartidor?.nombre);
        poner('nombre_ruta', data.ruta?.nombre);
        poner('vehiculo', `${data.vehiculo?.marca ?? '-'} - ${data.vehiculo?.placa ?? '-'}`);

        const minibodega = data.minibodega;
        const estado = elemento('estado_minibodega');

        if (minibodega?.id != null) {
            poner('minibodega', `MiniBodega #${minibodega.id}`);
            poner('estado_minibodega', minibodega.estado ? 'Activa' : 'Cerrada');
            estado.className = `badge ${minibodega.estado ? 'text-bg-success' : 'text-bg-danger'}`;
        } else {
            poner('minibodega', 'No encontrada');
            poner('estado_minibodega', '-');
            estado.className = 'badge text-bg-secondary';
        }
    }

    function mostrarJornada(jornada) {
        const ventas = jornada.ventas || {};
        const abonos = jornada.abonos || {};
        const devoluciones = jornada.devoluciones || {};
        const rotaciones = jornada.rotaciones || {};

        poner('fecha_jornada', jornada.fecha || '-');

        poner('cantidad_ventas', ventas.cantidad ?? 0);
        poner('dinero_ventas', dinero(ventas.dinero));
        poner('ventas_contado', dinero(ventas.contado));
        poner('ventas_credito', dinero(ventas.credito));

        poner('cantidad_abonos', abonos.cantidad ?? 0);
        poner('dinero_abonos', dinero(abonos.dinero));

        poner('cantidad_devoluciones', devoluciones.cantidad ?? 0);
        poner('dinero_devoluciones', dinero(devoluciones.dinero));
        poner('balance_devoluciones', balance(devoluciones.balance));
        poner('devoluciones_recibido', dinero(devoluciones.recibido));
        poner('devoluciones_entregado', dinero(devoluciones.entregado));

        poner('cantidad_rotaciones', rotaciones.cantidad ?? 0);
        poner('dinero_rotaciones', dinero(rotaciones.dinero));
        poner('balance_rotaciones', balance(rotaciones.balance));
        poner('rotaciones_recibido', dinero(rotaciones.recibido));
        poner('rotaciones_entregado', dinero(rotaciones.entregado));

        poner('efectivo_esperado', dinero(jornada.efectivo_esperado));
        poner('desglose_contado', dinero(ventas.contado));
        poner('desglose_abonos', dinero(abonos.dinero));
        poner('desglose_devoluciones', balance(devoluciones.balance));
        poner('desglose_rotaciones', balance(rotaciones.balance));
    }

    async function cargarDashboard() {
        try {
            const response = await fetch('/movil/dashboard/repartidor/api/');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();

            if (!data.success) {
                poner('nombre_repartidor', data.mensaje || 'No se pudo cargar la información.');
                return;
            }

            mostrarInformacion(data);
            mostrarJornada(data.jornada);
            mostrarInventario(data.inventario || []);
        } catch (error) {
            console.error('Error cargando dashboard del repartidor:', error);
            poner('nombre_repartidor', 'Error al cargar los datos');
            poner('tabla_inventario', 'Error al cargar el inventario.');
        }
    }

    cargarDashboard();
});
