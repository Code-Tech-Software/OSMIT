
document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("add-variacion");
    const container = document.getElementById("variaciones-container");
    const totalFormsInput = document.querySelector('[name$="-TOTAL_FORMS"]');
    const template = document.getElementById("empty-form-template").innerHTML;
    const existingVariations = container.querySelectorAll(".variacion-form");

    existingVariations.forEach(function (formDiv) {
        const deleteInput = formDiv.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput && deleteInput.checked) {
            formDiv.style.display = 'none';
        }
    });

    addButton.addEventListener("click", function () {
        let formCount = parseInt(totalFormsInput.value);
        let newFormHtml = template.replace(/__prefix__/g, formCount);
        container.insertAdjacentHTML("beforeend", newFormHtml);
        totalFormsInput.value = formCount + 1;
    });

    container.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-variacion")) {
            const formDiv = e.target.closest(".variacion-form");
            const deleteInput = formDiv.querySelector('input[name$="-DELETE"]');

            if (deleteInput) {
                deleteInput.checked = true;
                formDiv.style.display = 'none';
            } else {
                formDiv.remove();
            }
        }
    });
});
