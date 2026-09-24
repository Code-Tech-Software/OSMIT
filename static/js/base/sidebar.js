const menusItemsDropDown = document.querySelectorAll('.menu-item-dropdown');
const menusItemsStatic = document.querySelectorAll('.menu-item-static');
const sidebar = document.getElementById('sidebar');
const menuBtn = document.getElementById('menu-btn');
const sidebarBtn = document.getElementById('sidebar-btn');
const darkModeBtn = document.getElementById('dark-mode-btn');

// ===============================
// MODO OSCURO
// ===============================

if (darkModeBtn) {
darkModeBtn.addEventListener('click', () => {
document.body.classList.toggle('dark-mode');
});
}

// ===============================
// OCULTAR SIDEBAR COMPLETAMENTE
// ===============================

if (sidebarBtn) {
sidebarBtn.addEventListener('click', () => {
document.body.classList.toggle('sidebar-hidden');
});
}

// ===============================
// MINIMIZAR SIDEBAR
// ===============================

if (menuBtn && sidebar) {


menuBtn.addEventListener('click', () => {

    // Cambiar estado
    sidebar.classList.toggle('minimize');

    // Guardar el estado actual
    const estaMinimizado = sidebar.classList.contains('minimize');

    localStorage.setItem('sidebarMinimized', estaMinimizado);

});


}

// ===============================
// RESTAURAR ESTADO DEL SIDEBAR
// ===============================

function restaurarSidebar() {


if (!sidebar) return;

const estadoGuardado = localStorage.getItem('sidebarMinimized');

console.log('Estado guardado del sidebar:', estadoGuardado);

if (estadoGuardado === 'true') {

    sidebar.classList.add('minimize');

} else {

    sidebar.classList.remove('minimize');

}


}

// Restaurar estado al cargar la página
restaurarSidebar();

// ===============================
// MENÚS DESPLEGABLES
// ===============================

menusItemsDropDown.forEach((menuItem) => {


menuItem.addEventListener('click', () => {

    const subMenu = menuItem.querySelector('.sub-menu');

    const isActive = menuItem.classList.toggle('sub-menu-toggle');

    if (subMenu) {

        if (isActive) {

            subMenu.style.height = `${subMenu.scrollHeight + 6}px`;
            subMenu.style.padding = '0.2rem 0';

        } else {

            subMenu.style.height = '0';
            subMenu.style.padding = '0';

        }

    }


    // Cerrar los demás submenús
    menusItemsDropDown.forEach((item) => {

        if (item !== menuItem) {

            const otherSubmenu = item.querySelector('.sub-menu');

            if (otherSubmenu) {

                item.classList.remove('sub-menu-toggle');

                otherSubmenu.style.height = '0';
                otherSubmenu.style.padding = '0';

            }

        }

    });

});


});

// ===============================
// MENÚS ESTÁTICOS
// ===============================

menusItemsStatic.forEach((menuItem) => {


menuItem.addEventListener('mouseenter', () => {

    if (!sidebar.classList.contains('minimize')) return;


    menusItemsDropDown.forEach((item) => {

        const otherSubmenu = item.querySelector('.sub-menu');

        if (otherSubmenu) {

            item.classList.remove('sub-menu-toggle');

            otherSubmenu.style.height = '0';
            otherSubmenu.style.padding = '0';

        }

    });

});


});

// ===============================
// PANTALLA COMPLETA
// ===============================

const fullscreenToggle = document.getElementById("fullscreenToggle");

if (fullscreenToggle) {


fullscreenToggle.addEventListener("click", () => {

    if (!document.fullscreenElement) {

        document.documentElement.requestFullscreen().then(() => {

            fullscreenToggle.classList.remove("bi-arrows-fullscreen");
            fullscreenToggle.classList.add("bi-arrows-angle-contract");

        });

    } else {

        document.exitFullscreen().then(() => {

            fullscreenToggle.classList.remove("bi-arrows-angle-contract");
            fullscreenToggle.classList.add("bi-arrows-fullscreen");

        });

    }

});


// ===============================
// ACTUALIZAR ICONO DE PANTALLA COMPLETA
// ===============================

document.addEventListener("fullscreenchange", () => {

    if (!document.fullscreenElement) {

        fullscreenToggle.classList.remove("bi-arrows-angle-contract");
        fullscreenToggle.classList.add("bi-arrows-fullscreen");

    } else {

        fullscreenToggle.classList.remove("bi-arrows-fullscreen");
        fullscreenToggle.classList.add("bi-arrows-angle-contract");

    }

});


}
