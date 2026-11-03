
document.addEventListener('DOMContentLoaded', function () {
    const dashboard = document.getElementById('dashboard-granel');
    if (!dashboard) return;

    const graficas = [];

    function modoOscuro() {
        return document.body.classList.contains('dark-mode') ||
            document.documentElement.getAttribute('data-bs-theme') === 'dark' ||
            document.body.getAttribute('data-bs-theme') === 'dark';
    }

    function temaGrafica() {
        const oscuro = modoOscuro();
        return {
            mode: oscuro ? 'dark' : 'light',
            foreColor: oscuro ? '#e9ecef' : '#373d3f'
        };
    }

    function crearGrafica(selector, url, tipo) {
        const elemento = dashboard.querySelector(selector);
        if (!elemento) return;

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(data => {
                const tema = temaGrafica();
                const opciones = {
                    chart: {
                        type: tipo,
                        height: 350,
                        background: 'transparent',
                        foreColor: tema.foreColor
                    },
                    theme: { mode: tema.mode },
                    xaxis: {
                        categories: data.labels,
                        title: { text: tipo === 'bar' ? 'Producto' : 'Fecha' }
                    },
                    title: {
                        text: tipo === 'bar'
                            ? 'Productos con más salidas en los últimos 7 días'
                            : 'Cantidad de Productos Entrados vs Salidos (últimos 7 días)',
                        align: 'center'
                    },
                    grid: {
                        borderColor: modoOscuro() ? '#495057' : '#e7e7e7'
                    },
                    tooltip: { theme: tema.mode }
                };

                if (tipo === 'bar') {
                    opciones.series = [{
                        name: 'Cantidad Salida',
                        data: data.data
                    }];
                    opciones.colors = ['#FF4560', '#00E396', '#775DD0', '#FEB019', '#0090FF'];
                    opciones.plotOptions = {
                        bar: {
                            distributed: true,
                            borderRadius: 6,
                            columnWidth: '55%'
                        }
                    };
                } else {
                    opciones.series = [
                        { name: 'Entradas', data: data.entradas },
                        { name: 'Salidas', data: data.salidas }
                    ];
                    opciones.yaxis = { title: { text: 'Cantidad' } };
                    opciones.stroke = { curve: 'smooth' };
                    opciones.markers = { size: 5 };
                    opciones.colors = ['#00E396', '#FF4560'];
                }

                const grafica = new ApexCharts(elemento, opciones);
                graficas.push(grafica);
                grafica.render();
            })
            .catch(error => console.error(`Error cargando ${selector}:`, error));
    }

    function cargarIndicadores() {
        fetch('/granel/api/indicadores/')
            .then(res => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then(data => {
                dashboard.querySelector('#total_productos').textContent = data.total_productos;
                dashboard.querySelector('#productos_bajo_min').textContent = data.productos_bajo_min;
                dashboard.querySelector('#productos_sin_stock').textContent = data.productos_sin_stock;
                dashboard.querySelector('#pedidos_pendientes').textContent = data.pedidos_pendientes;
            })
            .catch(error => console.error('Error cargando indicadores de Granel:', error));
    }

    crearGrafica('#chart-top-productos', '/granel/api/top-productos-salidas/', 'bar');
    crearGrafica('#chart-entradas-salidas', '/granel/api/entradas-salidas/', 'line');
    cargarIndicadores();

    function actualizarTemaGraficas() {
        const tema = temaGrafica();
        graficas.forEach(grafica => {
            grafica.updateOptions({
                chart: { foreColor: tema.foreColor },
                theme: { mode: tema.mode },
                tooltip: { theme: tema.mode },
                grid: { borderColor: modoOscuro() ? '#495057' : '#e7e7e7' }
            }, false, false);
        });
    }

    const observador = new MutationObserver(actualizarTemaGraficas);
    observador.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme', 'class']
    });
    observador.observe(document.body, {
        attributes: true,
        attributeFilter: ['data-bs-theme', 'class']
    });
});
