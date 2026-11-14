
$(document).ready(function () {
    const contenedor = document.getElementById('registrarSalidaPT');
    if (!contenedor) return;

    const form = document.getElementById('salidaForm');
    const submitBtn = document.getElementById('submitBtn');
    const confirmSubmit = document.getElementById('confirmSubmit');
    const resumenSalida = document.getElementById('resumenSalida');
    const destinoSelect = document.getElementById('id_destino');
    const rutaSelect = document.getElementById('id_ruta');
    const contenedorRuta = document.getElementById('contenedorRuta');
    const ordenPersonalizado = document.getElementById('ordenPersonalizado');
    const tablaProductos = document.getElementById('productosTable');
    const confirmModalElement = document.getElementById('confirmModal');
    const confirmModal = bootstrap.Modal.getOrCreateInstance(confirmModalElement);
    const notyf = new Notyf({ duration: 3000, position: { x: 'right', y: 'bottom' }, dismissible: true });

    window.productosDT = $('#productosTable').DataTable({
        pageLength: 50,
        responsive: true,
        fixedHeader: { header: true, headerOffset: 70 },
        ordering: true,
        order: [],
        language: {
            decimal: '',
            emptyTable: 'No hay productos disponibles',
            info: 'Mostrando _START_ a _END_ de _TOTAL_ productos',
            infoEmpty: 'Mostrando 0 a 0 de 0 productos',
            infoFiltered: '(filtrado de _MAX_ productos en total)',
            lengthMenu: 'Mostrar _MENU_ productos',
            loadingRecords: 'Cargando...',
            processing: 'Procesando...',
            search: 'Buscar:',
            zeroRecords: 'No se encontraron productos coincidentes',
            paginate: {
                first: '<i class="bi bi-rewind-fill"></i>',
                last: '<i class="bi bi-fast-forward-fill"></i>',
                next: '<i class="bi bi-caret-right-fill"></i>',
                previous: '<i class="bi bi-caret-left-fill"></i>'
            }
        }
    });

    // Sincronizar encabezado flotante en tablets y celulares
    const scrollTablaPT = tablaProductos.closest('.table-responsive');
    if (scrollTablaPT) {
        const sincronizarHeaderPT = () => {
            if (window.innerWidth > 1199) return;
            const headerFlotante = document.querySelector('table.fixedHeader-floating');
            if (!headerFlotante) return;
            const tablaRect = tablaProductos.getBoundingClientRect();
            const headerRect = headerFlotante.getBoundingClientRect();
            const diferencia = headerRect.left - tablaRect.left;
            headerFlotante.style.width = `${tablaRect.width}px`;
            headerFlotante.style.transform = 'none';
            headerFlotante.style.marginLeft = '0';
            headerFlotante.style.left = `${headerFlotante.offsetLeft - diferencia}px`;
        };
        scrollTablaPT.addEventListener('scroll', sincronizarHeaderPT, { passive: true });
        window.addEventListener('resize', sincronizarHeaderPT);
        window.addEventListener('scroll', sincronizarHeaderPT, { passive: true });
    }

    // Evitar cambios accidentales en cantidades por scroll o flechas del teclado
    tablaProductos.addEventListener('wheel', function (e) {
        if (e.target.matches('input.cantidad-input')) e.target.blur();
    }, { passive: true });
    tablaProductos.addEventListener('keydown', function (e) {
        if (e.target.matches('input.cantidad-input') && ['ArrowUp', 'ArrowDown'].includes(e.key)) e.preventDefault();
    });

    // Cambio de orden de productos
    if (ordenPersonalizado) {
        ordenPersonalizado.addEventListener('change', function () {
            const url = new URL(window.location.href);
            url.searchParams.set('orden', this.checked ? 'personalizado' : 'alfabetico');
            window.location.href = url.toString();
        });
    }

    // Mostrar u ocultar la selección de ruta
    function toggleRutaRequisito() {
        if (!destinoSelect || !rutaSelect || !contenedorRuta) return;
        if (destinoSelect.value === 'opcion1') {
            contenedorRuta.style.display = 'block';
            rutaSelect.setAttribute('required', 'required');
        } else {
            contenedorRuta.style.display = 'none';
            rutaSelect.removeAttribute('required');
            rutaSelect.value = '';
        }
    }
    destinoSelect?.addEventListener('change', toggleRutaRequisito);
    toggleRutaRequisito();

    // Actualización automática del stock cada 5 segundos
    let actualizandoStockPT = false;
    async function actualizarStockPT() {
        if (actualizandoStockPT) return;
        actualizandoStockPT = true;
        try {
            const respuesta = await fetch(contenedor.dataset.urlStock, {
                method: 'GET',
                cache: 'no-store',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!respuesta.ok) throw new Error('No se pudo consultar el stock.');
            const datos = await respuesta.json();
            const stocks = datos.stocks || {};

            window.productosDT.$('input.cantidad-input').each(function () {
                const input = this;
                const variacionId = input.name.replace('cantidad_', '');
                const info = stocks[variacionId];
                if (!info) return;

                const nuevoStock = info.stock;
                const stockMin = info.stock_min;
                const stockAnterior = parseFloat(input.dataset.stock);
                if (stockAnterior === nuevoStock) return;

                input.dataset.stock = nuevoStock;
                input.max = nuevoStock;
                const stockValor = input.closest('td')?.querySelector('.stock-valor');
                if (stockValor) {
                    stockValor.textContent = nuevoStock;
                    stockValor.classList.remove('text-danger', 'text-warning', 'text-muted', 'fw-bold');
                    if (nuevoStock <= 0) {
                        stockValor.classList.add('text-danger', 'fw-bold');
                    } else if (nuevoStock <= stockMin) {
                        stockValor.classList.add('text-warning', 'fw-bold');
                    } else {
                        stockValor.classList.add('text-muted');
                    }
                }
                const cantidad = parseFloat(input.value);
                input.classList.toggle('is-invalid', !isNaN(cantidad) && cantidad > nuevoStock);
            });
        } catch (error) {
            console.warn('No se pudo actualizar el stock:', error);
        } finally {
            actualizandoStockPT = false;
        }
    }
    actualizarStockPT();
    setInterval(actualizarStockPT, 5000);

    // Evitar cantidades negativas y envío accidental con Enter
    form.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && e.target.tagName.toLowerCase() !== 'textarea') e.preventDefault();
    });
    $(tablaProductos).on('input', 'input.cantidad-input', function () {
        if (this.value !== '' && Number(this.value) < 0) this.value = 0;
    });

    // Validar productos y preparar el modal
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (destinoSelect?.value === 'opcion1' && (!rutaSelect || rutaSelect.value === '')) {
            notyf.error('Debes seleccionar una Ruta específica.');
            return;
        }

        const inputs = window.productosDT.$('input[name^="cantidad_"]');
        const rows = [];
        let errorStock = false;

        inputs.each(function () {
            const val = parseFloat(this.value);
            const maxStock = parseFloat(this.dataset.stock);
            if (isNaN(val) || val <= 0) return;
            if (val > maxStock) {
                errorStock = true;
                this.classList.add('is-invalid');
                return;
            }
            this.classList.remove('is-invalid');
            const nombre = this.dataset.prod;
            const presentacion = this.dataset.pres;
            const stock = this.dataset.stock;
            rows.push(`
                <tr>
                    <td class="text-start">${nombre}</td>
                    <td class="text-start">${presentacion}</td>
                    <td class="text-center">${stock}</td>
                    <td class="text-center fw-bold text-danger">-${val}</td>
                </tr>
            `);
        });

        if (errorStock) {
            notyf.error('Estás intentando sacar más productos del stock disponible.');
            return;
        }
        if (!rows.length) {
            notyf.error('Debes ingresar al menos una cantidad mayor a 0.');
            return;
        }

        const ruta = rutaSelect?.value ? rutaSelect.selectedOptions[0]?.text : 'N/A';
        const destino = destinoSelect?.selectedOptions[0]?.text || destinoSelect?.value;
        const nota = form.querySelector('[name="nota"]')?.value || '(Sin nota)';

        resumenSalida.innerHTML = `
            <div class="mb-3 p-3 bg-light rounded border border-danger-subtle resumen-datos">
                <div class="row">
                    <div class="col-md-6"><p class="mb-1"><strong>Destino:</strong> ${destino}</p></div>
                    <div class="col-md-6" style="display:${destinoSelect.value === 'opcion1' ? 'block' : 'none'}">
                        <p class="mb-1"><strong>Ruta:</strong> ${ruta}</p>
                    </div>
                </div>
                <p class="mb-0 mt-2"><strong>Nota:</strong> ${nota}</p>
            </div>
            <div class="table-responsive">
                <table class="table table-bordered table-sm">
                    <thead class="table-light text-center">
                        <tr>
                            <th class="text-start">Producto</th>
                            <th class="text-start">Presentación</th>
                            <th>Stock Actual</th>
                            <th>Cantidad a Salir</th>
                        </tr>
                    </thead>
                    <tbody>${rows.join('')}</tbody>
                </table>
            </div>
        `;
        confirmModal.show();
    });

    // Confirmar y registrar salida
    let registrandoSalida = false;
    let comprobandoAdvertencia = false;

    

    confirmSubmit.addEventListener('click', async function () {
        if (registrandoSalida || comprobandoAdvertencia) return;

        // Advertencia temporal: únicamente para salidas a Ruta
        if (destinoSelect?.value === 'opcion1') {
            comprobandoAdvertencia = true;
            confirmModal.hide();

            // Esperar a que Bootstrap termine de cerrar el modal
            await new Promise(resolve => {
                if (!confirmModalElement.classList.contains('show')) return resolve();
                confirmModalElement.addEventListener('hidden.bs.modal', resolve, { once: true });
            });

            let resultado;
            try {
                resultado = await Swal.fire({
                    title: '¿Ya te dieron autorización? 🤨',
                    html: `
                        <p>¿Estás segura de que ya puedes realizar la salida de esta ruta?</p>
                        <p class="fw-semibold">¡Recuerda que primero deben terminar los cortes o cerrar el inventario!</p>
                        <img src="${contenedor.dataset.gifAdvertencia}" alt="Advertencia"
                             class="img-fluid rounded mt-2" style="max-height:220px;">
                    `,
                    showCancelButton: true,
                    confirmButtonText: 'Sí, ya me autorizaron',
                    cancelButtonText: 'Mejor espero',
                    confirmButtonColor: '#dc3545',
                    reverseButtons: true
                });
            } catch (error) {
                console.error('Error al mostrar la advertencia:', error);
                comprobandoAdvertencia = false;
                confirmModal.show();
                return;
            }

            comprobandoAdvertencia = false;
            if (!resultado.isConfirmed) return;
        }

        registrandoSalida = true;
        const dt = window.productosDT;
        confirmSubmit.disabled = true;
        confirmSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Registrando...';
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Registrando...';

        dt.$('input[name^="cantidad_"]').each(function () {
            const valor = this.value;
            if (valor === '' || isNaN(parseFloat(valor)) || parseFloat(valor) <= 0) {
                this.removeAttribute('name');
            } else if (!document.contains(this)) {
                const hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = this.name;
                hidden.value = valor;
                form.appendChild(hidden);
            }
        });
        form.submit();
    });
});
