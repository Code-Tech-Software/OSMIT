// ==========================================================
// ELEMENTOS DEL SIDEBAR
// ==========================================================
const menusItemsDropDown = document.querySelectorAll('.menu-item-dropdown');
const menusItemsStatic = document.querySelectorAll('.menu-item-static');
const sidebar = document.getElementById('sidebar');
const menuBtn = document.getElementById('menu-btn');
const sidebarBtn = document.getElementById('sidebar-btn');
const darkModeBtn = document.getElementById('dark-mode-btn');

// ==========================================================
// MODO OSCURO
// ==========================================================
function aplicarTema(tema) {
    const oscuro = tema === 'dark';
    document.body.classList.toggle('dark-mode', oscuro);
    document.documentElement.setAttribute('data-bs-theme', tema);
    localStorage.setItem('osmit-theme', tema);
    if (darkModeBtn) {
        darkModeBtn.innerHTML = oscuro ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-stars-fill"></i>';
        darkModeBtn.setAttribute('aria-label', oscuro ? 'Activar modo claro' : 'Activar modo oscuro');
    }
}
aplicarTema(localStorage.getItem('osmit-theme') === 'dark' ? 'dark' : 'light');
if (darkModeBtn) darkModeBtn.addEventListener('click', () => {
    const oscuro = document.body.classList.contains('dark-mode');
    aplicarTema(oscuro ? 'light' : 'dark');
});

// ==========================================================
// OCULTAR SIDEBAR COMPLETAMENTE
// ==========================================================
if (sidebarBtn) sidebarBtn.addEventListener('click', () => document.body.classList.toggle('sidebar-hidden'));

// ==========================================================
// MINIMIZAR SIDEBAR
// ==========================================================
if (menuBtn && sidebar) menuBtn.addEventListener('click', () => {
    sidebar.classList.toggle('minimize');
    localStorage.setItem('sidebarMinimized', sidebar.classList.contains('minimize'));
});

// ==========================================================
// RESTAURAR ESTADO DEL SIDEBAR
// ==========================================================
function restaurarSidebar() {
    if (!sidebar) return;
    const movil = window.matchMedia('(max-width: 700px)').matches;
    const minimizado = localStorage.getItem('sidebarMinimized') === 'true';
    sidebar.classList.toggle('minimize', !movil && minimizado);
}
restaurarSidebar();

window.matchMedia('(max-width: 700px)').addEventListener('change', restaurarSidebar);

// ==========================================================
// MENÚS DESPLEGABLES
// ==========================================================
menusItemsDropDown.forEach(menuItem => {
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
        menusItemsDropDown.forEach(item => {
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

// ==========================================================
// MENÚS ESTÁTICOS
// ==========================================================
menusItemsStatic.forEach(menuItem => {
    menuItem.addEventListener('mouseenter', () => {
        if (!sidebar || !sidebar.classList.contains('minimize')) return;
        menusItemsDropDown.forEach(item => {
            const otherSubmenu = item.querySelector('.sub-menu');
            if (otherSubmenu) {
                item.classList.remove('sub-menu-toggle');
                otherSubmenu.style.height = '0';
                otherSubmenu.style.padding = '0';
            }
        });
    });
});

// ==========================================================
// PANTALLA COMPLETA
// ==========================================================
const fullscreenToggle = document.getElementById('fullscreenToggle');
if (fullscreenToggle) {
    fullscreenToggle.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().then(() => {
                fullscreenToggle.classList.remove('bi-arrows-fullscreen');
                fullscreenToggle.classList.add('bi-arrows-angle-contract');
            });
        } else {
            document.exitFullscreen().then(() => {
                fullscreenToggle.classList.remove('bi-arrows-angle-contract');
                fullscreenToggle.classList.add('bi-arrows-fullscreen');
            });
        }
    });
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            fullscreenToggle.classList.remove('bi-arrows-angle-contract');
            fullscreenToggle.classList.add('bi-arrows-fullscreen');
        } else {
            fullscreenToggle.classList.remove('bi-arrows-fullscreen');
            fullscreenToggle.classList.add('bi-arrows-angle-contract');
        }
    });
}

// ==========================================================
// BOTÓN RECARGAR
// ==========================================================
const reloadIcon = document.getElementById('reloadIcon');
if (reloadIcon) reloadIcon.addEventListener('click', function () {
    this.classList.add('spinning');
    setTimeout(() => location.reload(), 200);
});

// ==========================================================
// NOTIFICACIONES PUSHER
// PERMISOS RECIBIDOS DESDE SIDEBAR.HTML
// ==========================================================
const notificationConfig = document.getElementById('notification-config');
if (notificationConfig) {
    const puedeRecibirPedidos = notificationConfig.dataset.pedidos === 'true';
    const puedeRecibirReabastecimiento = notificationConfig.dataset.reabastecimiento === 'true';
    const notificationSound = new Audio(notificationConfig.dataset.sonido);
    notificationSound.load();

    let notificationsEnabled = JSON.parse(localStorage.getItem('notificationsEnabled')) ?? true;
    let soundEnabled = JSON.parse(localStorage.getItem('soundEnabled')) ?? true;
    const icon = document.getElementById('notificationToggle');

    function updateIcon() {
        if (!icon) return;
        if (notificationsEnabled && soundEnabled) {
            icon.className = 'bi fs-5 position-relative icon-hover bi-bell-fill';
        } else {
            icon.className = 'bi fs-5 position-relative icon-hover bi-bell-slash-fill text-muted';
        }
    }

    if (icon) {
        icon.addEventListener('click', () => {
            const turningOn = !(notificationsEnabled && soundEnabled);
            notificationsEnabled = turningOn;
            soundEnabled = turningOn;
            localStorage.setItem('notificationsEnabled', notificationsEnabled);
            localStorage.setItem('soundEnabled', soundEnabled);
            updateIcon();

            if (turningOn) {
                notificationSound.play().catch(e => {
                    console.warn('Sonido bloqueado, mostrando alerta:', e);
                    if (typeof Swal === 'undefined') return;
                    Swal.fire({
                        title: '🔊 Activa el sonido',
                        text: 'Haz clic en este mensaje para permitir notificaciones con audio.',
                        icon: 'info',
                        confirmButtonText: 'Activar sonido',
                        background: '#f0f9ff'
                    }).then(() => {
                        notificationSound.play().catch(err => console.log('Error persistente:', err));
                    });
                });
            }
        });
        updateIcon();
    }

    // ==========================================================
    // CONEXIÓN CON PUSHER
    // ==========================================================
    if (typeof Pusher !== 'undefined' && typeof Swal !== 'undefined') {
        const pusher = new Pusher('f15154bb7979deba25ba', {
            cluster: 'us2',
            encrypted: true
        });

        // TEMPORAL: Consultar el estado de Pusher desde la consola
        window.osmitPusher = pusher;

        // ======================================================
        // NOTIFICACIONES DE PEDIDOS - PRODUCTO A GRANEL
        // ======================================================
        if (puedeRecibirPedidos) {
            const channel = pusher.subscribe('pedidos-channel');
            channel.bind('nuevo-pedido', function (data) {
                if (!notificationsEnabled) return;

                const mensaje = `🛒 Nuevo pedido de <strong>${data.usuario}</strong> (ID: ${data.pedido_id})`;
                Swal.fire({
                    title: '¡Nuevo pedido!',
                    html: mensaje,
                    icon: 'success',
                    position: 'bottom-end',
                    background: '#343a40',
                    color: '#fff',
                    showConfirmButton: false,
                    timer: 9000,
                    toast: true
                });

                if (soundEnabled) {
                    notificationSound.play().catch(e => {
                        Swal.fire({
                            title: '🔔 Activa el sonido',
                            text: 'Haz clic para permitir notificaciones con audio.',
                            icon: 'info',
                            confirmButtonText: 'Entendido'
                        }).then(() => {
                            notificationSound.play().catch(err => console.log('Error persistente:', err));
                        });
                    });
                }
            });
        }

        // ======================================================
        // NOTIFICACIONES DE REABASTECIMIENTO - TERMINADO
        // ======================================================
        if (puedeRecibirReabastecimiento) {
            const reabastecimientoChannel = pusher.subscribe('reabastecimiento-channel');
            reabastecimientoChannel.bind('nuevo-reabastecimiento', function (data) {
                if (!notificationsEnabled) return;

                Swal.fire({
                    title: '¡Nuevo pedido de reabastecimiento!',
                    text: `El repartidor ${data.usuario} ha enviado un pedido.`,
                    icon: 'success',
                    position: 'bottom-end',
                    background: '#343a40',
                    color: '#fff',
                    showConfirmButton: false,
                    timer: 9000,
                    toast: true
                });

                if (soundEnabled) {
                    notificationSound.play().catch(e => {
                        Swal.fire({
                            title: '🔔 Activa el sonido',
                            text: 'Haz clic para permitir notificaciones con audio.',
                            icon: 'info',
                            confirmButtonText: 'Entendido'
                        }).then(() => {
                            notificationSound.play().catch(err => console.log('Error al reproducir sonido:', err));
                        });
                    });
                }
            });
        }
    } else {
        console.warn('No se cargaron Pusher o SweetAlert2. Las notificaciones en tiempo real no estarán disponibles.');
    }
}