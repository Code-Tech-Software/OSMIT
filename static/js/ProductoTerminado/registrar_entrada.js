
$(document).ready(function () {
    const contenedor = document.getElementById('registrarEntradaPT');
    if (!contenedor) return;

    const form = document.getElementById('entradaForm');
    const submitBtn = document.getElementById('submitBtn');
    const confirmSubmit = document.getElementById('confirmSubmit');
    const resumenEntrada = document.getElementById('resumenEntrada');
    const tablaProductos = document.getElementById('productosTable');
    const ordenPersonalizado = document.getElementById('ordenPersonalizado');
    const confirmModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('confirmModal'));
    const notyf = new Notyf({duration:2500, position:{x:'right',y:'bottom'}, dismissible:true});

    window.productosDT = $('#productosTable').DataTable({
        pageLength: 50,
        responsive: true,
        fixedHeader: {header:true, headerOffset:70},
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
                first:'<i class="bi bi-rewind-fill"></i>',
                last:'<i class="bi bi-fast-forward-fill"></i>',
                next:'<i class="bi bi-caret-right-fill"></i>',
                previous:'<i class="bi bi-caret-left-fill"></i>'
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
        scrollTablaPT.addEventListener('scroll', sincronizarHeaderPT, {passive:true});
        window.addEventListener('resize', sincronizarHeaderPT);
        window.addEventListener('scroll', sincronizarHeaderPT, {passive:true});
    }



    // Evitar cambios accidentales por rueda del mouse y teclas de dirección
    tablaProductos.addEventListener('wheel', function(e) {
        if (e.target.matches('input.cantidad-input')) e.target.blur();
    }, {passive:true});
    tablaProductos.addEventListener('keydown', function(e) {
        if (e.target.matches('input.cantidad-input') && ['ArrowUp','ArrowDown'].includes(e.key)) {
            e.preventDefault();
        }
    });

    // Evitar cantidades negativas
    $(tablaProductos).on('input', 'input.cantidad-input', function () {
        if (this.value !== '' && Number(this.value) < 0) this.value = 0;
    });

    // Evitar envío accidental con Enter
    form.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.tagName.toLowerCase() !== 'textarea') {
            e.preventDefault();
        }
    });

    // Cambiar entre orden personalizado y alfabético
    if (ordenPersonalizado) {
        ordenPersonalizado.addEventListener('change', function () {
            const url = new URL(window.location.href);
            url.searchParams.set('orden', this.checked ? 'personalizado' : 'alfabetico');
            window.location.href = url.toString();
        });
    }

    // Preparar modal de confirmación
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const inputs = window.productosDT.$('input[name^="cantidad_"]');
        const rows = [];

        inputs.each(function () {
            const valor = parseFloat(this.value);
            if (isNaN(valor) || valor <= 0) return;

            rows.push(`
                <tr>
                    <td class="text-start">${this.dataset.prod}</td>
                    <td class="text-start">${this.dataset.pres}</td>
                    <td class="text-center">${this.dataset.stock}</td>
                    <td class="text-center fw-bold">${valor}</td>
                </tr>
            `);
        });

        if (!rows.length) {
            notyf.error('Debes ingresar al menos una cantidad mayor a 0.');
            return;
        }

        const nota = document.getElementById('nota')?.value || '(Sin nota)';
        resumenEntrada.innerHTML = `
            <div class="mb-3 p-3 bg-light rounded resumen-nota">
                <p class="mb-0"><strong>Nota:</strong> ${nota}</p>
            </div>
            <div class="table-responsive">
                <table class="table table-bordered table-sm">
                    <thead class="table-light text-center">
                        <tr>
                            <th class="text-start">Producto</th>
                            <th class="text-start">Presentación</th>
                            <th>Stock Actual</th>
                            <th>Cantidad Ingreso</th>
                        </tr>
                    </thead>
                    <tbody>${rows.join('')}</tbody>
                </table>
            </div>
        `;
        confirmModal.show();
    });

    // Confirmar entrada y enviar todos los productos, incluso de otras páginas
    confirmSubmit.addEventListener('click', function () {
        confirmSubmit.disabled = true;
        confirmSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Registrando...';
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Registrando...';

        window.productosDT.$('input[name^="cantidad_"]').each(function () {
            const valor = parseFloat(this.value);
            if (isNaN(valor) || valor <= 0) {
                this.removeAttribute('name');
                return;
            }
            if (!document.contains(this)) {
                const hidden = document.createElement('input');
                hidden.type = 'hidden';
                hidden.name = this.name;
                hidden.value = this.value;
                form.appendChild(hidden);
            }
        });
        form.submit();
    });
});
