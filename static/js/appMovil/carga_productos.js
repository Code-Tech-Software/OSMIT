
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('csvUploadForm');
    const fileInput = document.getElementById('id_archivo_csv');
    if (!form || !fileInput) return;

    form.addEventListener('submit', function (event) {
        if (fileInput.files.length === 0) {
            alert('Por favor, selecciona un archivo antes de procesar.');
            event.preventDefault();
            return;
        }

        const archivo = fileInput.files[0];
        if (!archivo.name.toLowerCase().endsWith('.csv')) {
            alert('Formato no válido. Por favor, asegúrate de subir un archivo con extensión .csv');
            fileInput.value = '';
            event.preventDefault();
            return;
        }

        if (archivo.size > 5 * 1024 * 1024) {
            alert('El archivo es demasiado pesado. El límite máximo es de 5MB.');
            event.preventDefault();
            return;
        }

        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.classList.add('opacity-75');
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Procesando productos...';
    });
});
