
document.addEventListener('DOMContentLoaded', () => {
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

    document.querySelectorAll('.form-quitar-producto').forEach(form => {
        form.addEventListener('submit', e => {
            if (!confirm('¿Seguro que deseas quitar este producto de la MiniBodega?')) {
                e.preventDefault();
            }
        });
    });
});
