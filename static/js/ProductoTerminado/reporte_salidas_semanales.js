
document.addEventListener('DOMContentLoaded', () => {
    const reporte = document.getElementById('reporteSemanalPT');
    if (!reporte) return;

    const $ = id => document.getElementById(id);
    const listaSemanas = $('listaSemanas');
    const buscarSemana = $('buscarSemana');
    const btnSemanas = $('btnSemanas');
    const btnAplicarSemanas = $('btnAplicarSemanas');
    const btnLimpiarSemanas = $('btnLimpiarSemanas');
    const filtroDestino = $('filtroDestino');
    const filtroRuta = $('filtroRuta');
    const contenedorTablas = $('contenedorTablasSalidas');

    const urls = {
        semanas: reporte.dataset.urlSemanas,
        reporte: reporte.dataset.urlReporte,
        detalle: reporte.dataset.urlDetalle,
        resumen: reporte.dataset.urlResumen
    };
    const presentacionesReporte = ['Minis','Chico','Mediano','Grande','250g','500g','1kg','Kiosko','Grande 150g','Grande 140g','Pieza'];
    const gruposReporte = [
        {id:'NORMALES', titulo:'Productos normales'},
        {id:'ML', titulo:'Productos especiales ML'},
        {id:'Y', titulo:'Productos especiales Y'},
        {id:'YML', titulo:'Productos especiales YML'},
        {id:'YV', titulo:'Productos especiales YV'},
        {id:'JP', titulo:'Productos especiales JP'},
        {id:'N', titulo:'Productos especiales N'}
    ];
    const nombresMeses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
    const dias = [
        ['miercoles','totalMiercoles'],['jueves','totalJueves'],['viernes','totalViernes'],
        ['sabado','totalSabado'],['lunes','totalLunes'],['martes','totalMartes']
    ];
    const formatearNumero = n => Number(n || 0).toLocaleString('es-MX', {maximumFractionDigits:2});
    let semanasDisponibles = [];
    let semanasSeleccionadas = [];
    let solicitudReporte = 0;

    function formatearFecha(fecha) {
        if (!fecha) return '';
        const partes = fecha.split('-');
        return partes.length === 3 ? `${partes[2]}/${partes[1]}/${partes[0]}` : fecha;
    }
    function fechaLocalISO(fecha) {
        return `${fecha.getFullYear()}-${String(fecha.getMonth()+1).padStart(2,'0')}-${String(fecha.getDate()).padStart(2,'0')}`;
    }
    function obtenerSemanaActual() {
        const hoy = new Date();
        const inicio = new Date(hoy);
        inicio.setDate(hoy.getDate() - ((hoy.getDay() - 3 + 7) % 7));
        const fin = new Date(inicio);
        fin.setDate(inicio.getDate() + 6);
        return {inicio:fechaLocalISO(inicio), fin:fechaLocalISO(fin)};
    }
    function textoPeriodo() {
        if (semanasSeleccionadas.length) return `${semanasSeleccionadas.length} semanas seleccionadas`;
        const semana = obtenerSemanaActual();
        return `Semana del ${formatearFecha(semana.inicio)} al ${formatearFecha(semana.fin)}`;
    }
    function parametroSemanas() {
        return semanasSeleccionadas.join(',');
    }
    function actualizarTextoBotonSemanas() {
        if (!semanasSeleccionadas.length) {
            btnSemanas.textContent = 'Semana actual';
        } else if (semanasSeleccionadas.length === 1) {
            const semana = semanasDisponibles.find(s => s.inicio === semanasSeleccionadas[0]);
            btnSemanas.textContent = semana
                ? `Semana del ${formatearFecha(semana.inicio)} al ${formatearFecha(semana.fin)}`
                : '1 semana seleccionada';
        } else {
            btnSemanas.textContent = `${semanasSeleccionadas.length} semanas seleccionadas`;
        }
    }
    function actualizarSeleccionSemanas() {
        listaSemanas.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            if (checkbox.checked && !semanasSeleccionadas.includes(checkbox.value)) {
                semanasSeleccionadas.push(checkbox.value);
            } else if (!checkbox.checked) {
                semanasSeleccionadas = semanasSeleccionadas.filter(fecha => fecha !== checkbox.value);
            }
        });
        actualizarTextoBotonSemanas();
    }
    function renderizarSemanas() {
        const busqueda = buscarSemana.value.toLowerCase().trim();
        listaSemanas.replaceChildren();
        if (!semanasDisponibles.length) {
            listaSemanas.innerHTML = '<div class="text-center text-muted">No hay semanas disponibles.</div>';
            return;
        }
        const filtradas = semanasDisponibles.filter(semana => {
            const mes = Number(semana.inicio.split('-')[1]) - 1;
            const texto = `${semana.inicio} ${semana.fin} ${formatearFecha(semana.inicio)} ${formatearFecha(semana.fin)} ${semana.anio} ${nombresMeses[mes]}`.toLowerCase();
            return texto.includes(busqueda);
        });
        if (!filtradas.length) {
            listaSemanas.innerHTML = '<div class="text-center text-muted">No se encontraron semanas.</div>';
            return;
        }
        const grupos = {};
        filtradas.forEach(semana => {
            const [anio, mes] = semana.inicio.split('-').map(Number);
            if (!grupos[anio]) grupos[anio] = {};
            if (!grupos[anio][mes]) grupos[anio][mes] = [];
            grupos[anio][mes].push(semana);
        });
        Object.keys(grupos).sort((a,b) => Number(b)-Number(a)).forEach(anio => {
            const tituloAnio = document.createElement('div');
            tituloAnio.className = 'fw-bold fs-5 mt-3 mb-2 border-bottom pb-1';
            tituloAnio.textContent = anio;
            listaSemanas.appendChild(tituloAnio);

            Object.keys(grupos[anio]).sort((a,b) => Number(b)-Number(a)).forEach(mes => {
                const tituloMes = document.createElement('div');
                tituloMes.className = 'fw-semibold text-primary mt-3 mb-2 ms-2';
                tituloMes.textContent = nombresMeses[Number(mes)-1];
                listaSemanas.appendChild(tituloMes);

                grupos[anio][mes].sort((a,b) => b.inicio.localeCompare(a.inicio)).forEach(semana => {
                    const contenedor = document.createElement('div');
                    contenedor.className = 'form-check mb-2 ms-3';
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.className = 'form-check-input';
                    checkbox.value = semana.inicio;
                    checkbox.id = `semana-${semana.inicio}`;
                    checkbox.checked = semanasSeleccionadas.includes(semana.inicio);
                    checkbox.addEventListener('change', actualizarSeleccionSemanas);
                    const label = document.createElement('label');
                    label.className = 'form-check-label';
                    label.htmlFor = checkbox.id;
                    label.textContent = `Semana del ${formatearFecha(semana.inicio)} al ${formatearFecha(semana.fin)}`;
                    contenedor.append(checkbox, label);
                    listaSemanas.appendChild(contenedor);
                });
            });
        });
    }
    async function cargarSemanasDisponibles() {
        listaSemanas.innerHTML = '<div class="text-center text-muted">Cargando semanas...</div>';
        try {
            const response = await fetch(urls.semanas);
            if (!response.ok) throw new Error('Error al obtener las semanas');
            const data = await response.json();
            semanasDisponibles = data.semanas || [];
            renderizarSemanas();
        } catch (error) {
            console.error(error);
            listaSemanas.innerHTML = '<div class="text-center text-danger">No fue posible cargar las semanas.</div>';
        }
    }
    function actualizarFiltroRuta() {
        $('contenedorFiltroRuta').classList.toggle('d-none', filtroDestino.value !== 'opcion1');
    }
    function identificarGrupo(item) {
        if (item.grupo) return item.grupo;
        const nombre = (item.producto || '').trim().toUpperCase();
        for (const prefijo of ['ML ','YML ','YV ','JP ','Y ','N ']) {
            if (nombre.startsWith(prefijo)) return prefijo.trim();
        }
        return 'NORMALES';
    }
    function crearTablaGrupo(grupo, productos, destino) {
        const tarjeta = document.createElement('div');
        tarjeta.className = 'card grupo-reporte-pt';
        const encabezado = document.createElement('div');
        encabezado.className = 'card-header bg-light';
        encabezado.textContent = grupo.titulo;
        tarjeta.appendChild(encabezado);

        const cuerpo = document.createElement('div');
        cuerpo.className = 'card-body';
        const contenedor = document.createElement('div');
        contenedor.className = 'table-responsive';
        const tabla = document.createElement('table');
        tabla.className = 'table table-bordered table-sm table-hover align-middle tabla-semanal-pt';

        const presentes = new Set(productos.map(p => (p.presentacion || '').trim().toUpperCase()));
        const adicionales = [...new Set(productos.map(p => (p.presentacion || '').trim()).filter(Boolean))]
            .filter(p => !presentacionesReporte.some(normal => normal.toUpperCase() === p.toUpperCase()))
            .sort((a,b) => a.localeCompare(b,'es'));
        const columnas = grupo.id === 'NORMALES'
            ? [...presentacionesReporte, ...adicionales]
            : [...presentacionesReporte.filter(p => presentes.has(p.toUpperCase())), ...adicionales];

        const thead = document.createElement('thead');
        const filaEncabezado = document.createElement('tr');
        ['Producto', ...columnas, 'Total'].forEach(nombre => {
            const th = document.createElement('th');
            th.textContent = nombre;
            filaEncabezado.appendChild(th);
        });
        thead.appendChild(filaEncabezado);
        tabla.appendChild(thead);

        const tbody = document.createElement('tbody');
        const productosAgrupados = new Map();
        productos.forEach(item => {
            const nombre = item.producto || '';
            if (!productosAgrupados.has(nombre)) productosAgrupados.set(nombre, new Map());
            const clave = (item.presentacion || '').trim().toUpperCase();
            if (!productosAgrupados.get(nombre).has(clave)) productosAgrupados.get(nombre).set(clave, []);
            productosAgrupados.get(nombre).get(clave).push(item);
        });

        const totalesColumnas = Array(columnas.length).fill(0);
        let totalGrupo = 0;
        productosAgrupados.forEach((variaciones, nombre) => {
            const fila = document.createElement('tr');
            const celdaProducto = document.createElement('td');
            celdaProducto.textContent = nombre;
            fila.appendChild(celdaProducto);
            let totalFila = 0;

            columnas.forEach((presentacion,i) => {
                const items = variaciones.get(presentacion.toUpperCase()) || [];
                const cantidad = items.reduce((suma,item) => suma + Number(item.total_salido || 0), 0);
                totalFila += cantidad;
                totalesColumnas[i] += cantidad;
                const celda = document.createElement('td');
                celda.className = 'text-center';
                celda.textContent = cantidad ? formatearNumero(cantidad) : '–';
                if (cantidad && items.length === 1 && (destino === 'opcion1' || destino === 'todos')) {
                    celda.classList.add('celda-clic');
                    celda.title = 'Ver detalle por día';
                    celda.addEventListener('click', () => {
                        if (destino === 'opcion1') abrirDetalleProducto(items[0]);
                        else abrirResumenDestinos(items[0]);
                    });
                }
                fila.appendChild(celda);
            });
            totalGrupo += totalFila;
            const celdaTotal = document.createElement('td');
            celdaTotal.className = 'text-center fw-bold';
            celdaTotal.textContent = formatearNumero(totalFila);
            fila.appendChild(celdaTotal);
            tbody.appendChild(fila);
        });
        tabla.appendChild(tbody);

        const tfoot = document.createElement('tfoot');
        const filaTotal = document.createElement('tr');
        ['Total', ...totalesColumnas.map(formatearNumero), formatearNumero(totalGrupo)].forEach((valor,i) => {
            const celda = document.createElement('td');
            celda.className = i ? 'text-center' : '';
            celda.textContent = valor;
            filaTotal.appendChild(celda);
        });
        tfoot.appendChild(filaTotal);
        tabla.appendChild(tfoot);
        contenedor.appendChild(tabla);
        cuerpo.appendChild(contenedor);
        tarjeta.appendChild(cuerpo);
        return {tarjeta, total:totalGrupo};
    }
    async function cargarReporte() {
        const solicitud = ++solicitudReporte;
        const destino = filtroDestino.value;
        const ruta = filtroRuta.value;
        actualizarFiltroRuta();
        contenedorTablas.innerHTML = '<div class="card"><div class="card-body text-center">Cargando reporte...</div></div>';
        try {
            const params = new URLSearchParams({destino});
            if (destino === 'opcion1') params.set('ruta', ruta);
            if (parametroSemanas()) params.set('semanas', parametroSemanas());
            const response = await fetch(`${urls.reporte}?${params}`);
            if (!response.ok) throw new Error('Error al obtener el reporte');
            const data = await response.json();
            if (solicitud !== solicitudReporte) return;
            $('periodoSemana').textContent = textoPeriodo();
            contenedorTablas.replaceChildren();

            if (!data.productos?.length) {
                contenedorTablas.innerHTML = '<div class="card"><div class="card-body text-center text-muted">No hubo salidas durante el periodo seleccionado.</div></div>';
                return;
            }
            let totalGeneral = 0;
            gruposReporte.forEach(grupo => {
                const productos = data.productos.filter(item => identificarGrupo(item) === grupo.id);
                if (!productos.length) return;
                const resultado = crearTablaGrupo(grupo, productos, destino);
                contenedorTablas.appendChild(resultado.tarjeta);
                totalGeneral += resultado.total;
            });
            const resumen = document.createElement('div');
            resumen.className = 'card border-primary';
            resumen.innerHTML = `<div class="card-body d-flex justify-content-between align-items-center"><strong>Total general de salidas</strong><strong class="fs-5 text-primary">${formatearNumero(totalGeneral)}</strong></div>`;
            contenedorTablas.appendChild(resumen);
        } catch (error) {
            if (solicitud !== solicitudReporte) return;
            console.error(error);
            contenedorTablas.innerHTML = '<div class="card"><div class="card-body text-center text-danger">No fue posible cargar el reporte.</div></div>';
        }
    }
    function urlDetalle(base, id) {
        return base.replace(/\/0(?=\/|$)/, `/${encodeURIComponent(id)}`);
    }
    function abrirModal(id) {
        const modal = bootstrap.Modal.getOrCreateInstance($(id));
        modal.show();
    }
    function crearCelda(valor, clase = '') {
        const celda = document.createElement('td');
        celda.textContent = valor;
        if (clase) celda.className = clase;
        return celda;
    }
    function mostrarFilaEstado(tbody, mensaje, clase = '') {
        tbody.replaceChildren();
        const fila = document.createElement('tr');
        const celda = crearCelda(mensaje, `text-center ${clase}`);
        celda.colSpan = 8;
        fila.appendChild(celda);
        tbody.appendChild(fila);
    }
    async function abrirDetalleProducto(item) {
        $('modalDetalleProductoLabel').textContent = `${item.producto} - ${item.presentacion}`;
        $('modalProductoInfo').textContent = `Producto: ${item.producto} | Presentación: ${item.presentacion}`;
        $('modalPeriodo').textContent = textoPeriodo();
        const tabla = $('tablaDetalleProducto');
        mostrarFilaEstado(tabla, 'Cargando...');
        abrirModal('modalDetalleProducto');

        try {
            const params = new URLSearchParams({destino:filtroDestino.value});
            if (filtroDestino.value === 'opcion1') params.set('ruta', filtroRuta.value);
            if (parametroSemanas()) params.set('semanas', parametroSemanas());
            const response = await fetch(`${urlDetalle(urls.detalle, item.producto_variacion_id)}?${params}`);
            if (!response.ok) throw new Error('Error al obtener el detalle');
            const data = await response.json();
            tabla.replaceChildren();
            if (!data.repartidores?.length) {
                mostrarFilaEstado(tabla, 'No hay movimientos de Ruta para este producto durante las semanas seleccionadas.');
                return;
            }
            data.repartidores.forEach(repartidor => {
                const fila = document.createElement('tr');
                [repartidor.repartidor,repartidor.miercoles,repartidor.jueves,
                 repartidor.viernes,repartidor.sabado,repartidor.lunes,
                 repartidor.martes,repartidor.total].forEach((valor,i) => {
                    fila.appendChild(crearCelda(valor, i === 7 ? 'fw-bold' : ''));
                });
                tabla.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
            mostrarFilaEstado(tabla, 'No fue posible cargar el detalle.', 'text-danger');
        }
    }
    async function abrirResumenDestinos(item) {
        $('modalResumenDestinosLabel').textContent = `${item.producto} - ${item.presentacion}`;
        $('modalResumenProductoInfo').textContent = `Producto: ${item.producto} | Presentación: ${item.presentacion}`;
        $('modalResumenPeriodo').textContent = textoPeriodo();
        const tabla = $('tablaResumenDestinos');
        mostrarFilaEstado(tabla, 'Cargando...');
        dias.forEach(([,id]) => $(id).textContent = '0');
        $('totalResumenDestinos').textContent = '0';
        abrirModal('modalResumenDestinos');

        try {
            const params = new URLSearchParams();
            if (parametroSemanas()) params.set('semanas', parametroSemanas());
            const query = params.toString();
            const url = urlDetalle(urls.resumen, item.producto_variacion_id) + (query ? `?${query}` : '');
            const response = await fetch(url);
            if (!response.ok) throw new Error('Error al obtener el resumen');
            const data = await response.json();
            tabla.replaceChildren();
            const destinos = data.destinos || [];
            if (!destinos.length) mostrarFilaEstado(tabla, 'No hay salidas en el periodo seleccionado.');
            destinos.forEach(destino => {
                const fila = document.createElement('tr');
                fila.appendChild(crearCelda(destino.nombre, 'text-start fw-semibold'));
                dias.forEach(([dia]) => fila.appendChild(crearCelda(formatearNumero(destino[dia]))));
                fila.appendChild(crearCelda(formatearNumero(destino.total), 'fw-bold'));
                tabla.appendChild(fila);
            });
            const totales = data.totales_dias || {};
            dias.forEach(([dia,id]) => $(id).textContent = formatearNumero(totales[dia]));
            $('totalResumenDestinos').textContent = formatearNumero(data.total);
        } catch (error) {
            console.error(error);
            mostrarFilaEstado(tabla, 'No fue posible cargar el resumen.', 'text-danger');
        }
    }

    btnAplicarSemanas.addEventListener('click', () => {
        cargarReporte();
        bootstrap.Dropdown.getInstance(btnSemanas)?.hide();
    });
    btnLimpiarSemanas.addEventListener('click', () => {
        semanasSeleccionadas = [];
        renderizarSemanas();
        actualizarTextoBotonSemanas();
    });
    buscarSemana.addEventListener('input', renderizarSemanas);
    filtroDestino.addEventListener('change', cargarReporte);
    filtroRuta.addEventListener('change', cargarReporte);

    actualizarFiltroRuta();
    cargarSemanasDisponibles();
    cargarReporte();
});
