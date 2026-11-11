
document.addEventListener('DOMContentLoaded', () => {
    // =========================================================
    // SELECTS DEPENDIENTES: PRODUCTOS Y PRESENTACIONES
    // =========================================================
    const productoSelect = document.getElementById('productoSelect');
    const variacionSelect = document.getElementById('variacionSelect');
    const dataElement = document.getElementById('productos-minibodega-data');

    if (productoSelect && variacionSelect && dataElement) {
        const productos = JSON.parse(dataElement.textContent);

        productoSelect.addEventListener('change', () => {
            const producto = productos.find(p => String(p.id) === productoSelect.value);
            variacionSelect.replaceChildren(new Option(
                producto ? 'Seleccionar presentación...' : 'Primero selecciona un producto', ''
            ));
            variacionSelect.disabled = !producto;
            if (!producto) return;

            producto.variaciones.forEach(variacion => {
                variacionSelect.add(new Option(variacion.nombre, variacion.id));
            });
        });
    }

    // =========================================================
    // MODIFICACIÓN MASIVA DE CANTIDADES
    // =========================================================
    const formMasivo = document.getElementById('form-cantidades-masivas');
    let hayCambiosPendientes = () => false;

    if (formMasivo) {
        const inputs = [...formMasivo.querySelectorAll('.cantidad-editable')];
        const contador = document.getElementById('contadorCambios');
        const boton = document.getElementById('btnGuardarCantidades');
        const originales = new Map(inputs.map(input => [input.name, input.value]));

        const obtenerModificados = () => inputs.filter(input => {
            const original = originales.get(input.name);
            return input.value !== original && Number(input.value) !== Number(original);
        });

        hayCambiosPendientes = () => obtenerModificados().length > 0;

        function actualizarCambios() {
            const modificados = obtenerModificados();
            const productos = new Set(modificados.map(input => input.name.split('_').at(-1)));
            const cantidad = productos.size;

            contador.textContent = cantidad
                ? `${cantidad} producto${cantidad !== 1 ? 's' : ''} modificado${cantidad !== 1 ? 's' : ''}`
                : 'Sin cambios pendientes';

            boton.disabled = cantidad === 0;

            inputs.forEach(input => {
                const original = originales.get(input.name);
                const modificado = input.value !== original && Number(input.value) !== Number(original);
                input.classList.toggle('border-warning', modificado);
            });
        }

        inputs.forEach(input => input.addEventListener('input', actualizarCambios));

        formMasivo.addEventListener('submit', event => {
            const cantidad = new Set(obtenerModificados().map(input => input.name.split('_').at(-1))).size;
            if (!cantidad || !confirm(`¿Deseas guardar los cambios de ${cantidad} producto(s)?`)) {
                event.preventDefault();
            }
        });
    }

    // =========================================================
    // QUITAR PRODUCTO (SE CONSERVA)
    // =========================================================
    document.querySelectorAll('.form-quitar-producto').forEach(form => {
        form.addEventListener('submit', event => {
            if (hayCambiosPendientes()) {
                if (!confirm('Tienes cantidades modificadas sin guardar. Si continúas, perderás esos cambios. ¿Deseas continuar?')) {
                    event.preventDefault();
                    return;
                }
            }

            if (!confirm('¿Seguro que deseas quitar este producto de la MiniBodega?')) {
                event.preventDefault();
            }
        });
    });
});
