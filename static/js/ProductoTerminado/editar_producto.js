
document.addEventListener("DOMContentLoaded", function () {
    const btnAdd = document.getElementById("btn-add-variacion");
    const container = document.getElementById("variaciones-container");
    const template = document.getElementById("empty-form-template").innerHTML;

    // Django usa el prefijo del formset para identificar el total de formularios
    const totalFormsInput = document.getElementById("id_variaciones-TOTAL_FORMS");

    btnAdd.addEventListener("click", function (e) {
        e.preventDefault();
        let currentFormCount = parseInt(totalFormsInput.value);
        let newFormHtml = template.replace(/__prefix__/g, currentFormCount);
        container.insertAdjacentHTML('beforeend', newFormHtml);
        totalFormsInput.value = currentFormCount + 1;
    });
});
