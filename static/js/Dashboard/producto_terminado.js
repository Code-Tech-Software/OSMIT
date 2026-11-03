
document.addEventListener('DOMContentLoaded', function () {
    const dashboard = document.getElementById('dashboard-producto-terminado');
    if (!dashboard) return;

    let grafica = null;
    let ultimoTemaAplicado = null;

    function modoOscuro() {
        return document.body.classList.contains('dark-mode') ||
            document.documentElement.getAttribute('data-bs-theme') === 'dark' ||
            document.body.getAttribute('data-bs-theme') === 'dark';
    }

    function temaGrafica() {
        const oscuro = modoOscuro();
        return {
            mode: oscuro ? 'dark' : 'light',
            foreColor: oscuro ? '#e9ecef' : '#373d3f',
            gridColor: oscuro ? '#495057' : '#e7e7e7'
        };
    }

    async function cargarIndicadores() {
        try {
            const res = await fetch('/terminado/api/indicadoresPT/');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            dashboard.querySelector('#total_productos').textContent = data.total_productos;
            dashboard.querySelector('#productos_bajo_min').textContent = data.productos_bajo_min;
            dashboard.querySelector('#productos_sin_stock').textContent = data.productos_sin_stock;
            dashboard.querySelector('#pedidos_pendientes').textContent = data.pedidos_pendientes;
        } catch (error) {
            console.error('Error cargando indicadores de Producto Terminado:', error);
        }
    }

    async function cargarGrafica() {
        try {
            const res = await fetch('/terminado/api/entradas-salidas/PT/');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const tema = temaGrafica();

            const options = {
                chart: {
                    type: 'line',
                    height: 350,
                    background: 'transparent',
                    foreColor: tema.foreColor
                },
                theme: { mode: tema.mode },
                series: [
                    { name: 'Entradas', data: data.entradas },
                    { name: 'Salidas', data: data.salidas }
                ],
                xaxis: {
                    categories: data.labels,
                    title: { text: 'Fecha' }
                },
                yaxis: {
                    title: { text: 'Cantidad' }
                },
                title: {
                    text: 'Cantidad de Productos Entrados vs Salidos (últimos 7 días)',
                    align: 'center'
                },
                stroke: { curve: 'smooth' },
                markers: { size: 5 },
                colors: ['#00E396', '#FF4560'],
                grid: { borderColor: tema.gridColor },
                tooltip: { theme: tema.mode }
            };

            grafica = new ApexCharts(dashboard.querySelector('#chart-entradas-salidas'), options);
            await grafica.render();
            ultimoTemaAplicado = tema.mode;
        } catch (error) {
            console.error('Error cargando gráfica de Producto Terminado:', error);
        }
    }

    function actualizarTemaGrafica() {
        if (!grafica) return;

        const tema = temaGrafica();

        // No actualizar si el modo claro/oscuro sigue siendo el mismo
        if (ultimoTemaAplicado === tema.mode) return;

        ultimoTemaAplicado = tema.mode;

        grafica.updateOptions({
            chart: { foreColor: tema.foreColor },
            theme: { mode: tema.mode },
            grid: { borderColor: tema.gridColor },
            tooltip: { theme: tema.mode }
        }, false, false);
    }

    cargarIndicadores();
    cargarGrafica();

    const observador = new MutationObserver(actualizarTemaGrafica);
    observador.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme', 'class']
    });
    observador.observe(document.body, {
        attributes: true,
        attributeFilter: ['data-bs-theme', 'class']
    });
});
