
document.addEventListener("DOMContentLoaded", function () {
    const reporte = document.getElementById("reporteDiarioPT");
    if (!reporte) return;

    const filtroMovimiento = document.getElementById("filtroMovimiento");
    const filtroFecha = document.getElementById("filtroFecha");
    const filtroDestino = document.getElementById("filtroDestino");
    const filtroTipoProducto = document.getElementById("filtroTipoProducto");
    const filtroEspecial = document.getElementById("filtroEspecial");
    const contenedorDestino = document.getElementById("contenedorDestino");
    const contenedorEspecial = document.getElementById("contenedorEspecial");
    const btnConsultar = document.getElementById("btnConsultar");
    const btnDescargarImagen = document.getElementById("btnDescargarImagen");
    const encabezadoTabla = document.getElementById("encabezadoTabla");
    const cuerpoTabla = document.getElementById("cuerpoTabla");
    const pieTabla = document.getElementById("pieTabla");
    const tituloReporte = document.getElementById("tituloReporte");
    const subtituloReporte = document.getElementById("subtituloReporte");
    const indicadorCarga = document.getElementById("indicadorCarga");
    const mostrarStock = document.getElementById("mostrarStock");

    const urlDatos = reporte.dataset.urlDatos;
    let solicitudActual = 0;
    let datosReporteActual = null;
    let generandoImagen = false;

    const nombresDestinos = {
        general: "General",
        opcion1: "Ruta",
        opcion2: "Mitsu",
        opcion3: "Maestro",
        opcion4: "Otros"
    };

    function formatearCantidad(valor) {
        const numero = Number(valor || 0);
        return numero.toLocaleString("es-MX", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }

    function actualizarFiltros() {
        const esSalida = filtroMovimiento.value === "salidas";
        const esEspecial = filtroTipoProducto.value === "especial";
        contenedorDestino.classList.toggle("d-none", !esSalida);
        contenedorEspecial.classList.toggle("d-none", !esEspecial);
    }

    function crearCelda(texto, etiqueta = "td", clase = "") {
        const celda = document.createElement(etiqueta);
        celda.textContent = texto;
        if (clase) celda.className = clase;
        return celda;
    }

    function mostrarError(mensaje) {
        datosReporteActual = null;
        encabezadoTabla.replaceChildren(crearCelda("Producto", "th"));
        cuerpoTabla.replaceChildren();
        pieTabla.replaceChildren();

        const fila = document.createElement("tr");
        fila.appendChild(crearCelda(mensaje, "td", "text-center text-danger"));
        cuerpoTabla.appendChild(fila);
    }

    function renderizarTabla(data) {
        encabezadoTabla.replaceChildren();
        cuerpoTabla.replaceChildren();
        pieTabla.replaceChildren();

        encabezadoTabla.appendChild(crearCelda("Producto", "th"));

        data.presentaciones.forEach(presentacion => {
            encabezadoTabla.appendChild(crearCelda(presentacion, "th"));
        });
        encabezadoTabla.appendChild(crearCelda("Total", "th", "col-total"));

        if (data.productos.length === 0) {
            const fila = document.createElement("tr");
            const celda = crearCelda(
                "No se encontraron movimientos para la fecha seleccionada.",
                "td", "text-center text-muted py-4"
            );
            celda.colSpan = data.presentaciones.length + 2;
            fila.appendChild(celda);
            cuerpoTabla.appendChild(fila);
            return;
        }

        data.productos.forEach(producto => {
            const fila = document.createElement("tr");
            fila.appendChild(crearCelda(producto.producto));

            producto.cantidades.forEach((cantidad, indice) => {
                const celda = document.createElement("td");

                if (!producto.variaciones_existentes[indice]) {
                    fila.appendChild(celda);
                    return;
                }

                const contenedor = document.createElement("div");
                contenedor.className = "celda-cantidades";

                const cantidadPrincipal = document.createElement("span");
                cantidadPrincipal.className = "cantidad-movimiento";
                cantidadPrincipal.textContent = Number(cantidad) === 0
                    ? "-" : formatearCantidad(cantidad);
                contenedor.appendChild(cantidadPrincipal);

                if (mostrarStock.checked) {
                    const cantidadStock = document.createElement("span");
                    cantidadStock.className = "cantidad-stock";
                    cantidadStock.textContent = "/ " + formatearCantidad(producto.stocks[indice]);
                    contenedor.appendChild(cantidadStock);
                }

                celda.appendChild(contenedor);
                fila.appendChild(celda);
            });

            fila.appendChild(crearCelda(formatearCantidad(producto.total), "td", "col-total"));
            cuerpoTabla.appendChild(fila);
        });

        const filaTotales = document.createElement("tr");
        filaTotales.appendChild(crearCelda("TOTAL GENERAL", "td"));

        data.totales_presentaciones.forEach(total => {
            filaTotales.appendChild(crearCelda(formatearCantidad(total), "td"));
        });
        filaTotales.appendChild(crearCelda(formatearCantidad(data.total_general), "td", "col-total"));
        pieTabla.appendChild(filaTotales);
    }

    async function descargarImagenReporte() {
        if (!datosReporteActual || !datosReporteActual.productos.length) {
            alert("No hay datos para descargar.");
            return;
        }
        if (btnConsultar.disabled) {
            alert("Espera a que termine de cargar el reporte.");
            return;
        }
        if (generandoImagen) return;

        generandoImagen = true;
        btnDescargarImagen.disabled = true;
        const textoOriginal = btnDescargarImagen.innerHTML;
        btnDescargarImagen.textContent = "Generando imagen...";
        let contenedor = null;

        try {
            if (typeof html2canvas === "undefined") {
                throw new Error("No se pudo cargar html2canvas.");
            }

            const ahora = new Date();
            const fechaCaptura = ahora.toLocaleString("es-MX", {
                day: "2-digit", month: "2-digit", year: "numeric",
                hour: "2-digit", minute: "2-digit", second: "2-digit",
                hour12: false
            });

            const data = datosReporteActual;
            const movimiento = data.movimiento;
            const destino = data.destino;
            const fechaReporte = data.fecha.split("-").reverse().join("/");
            const tablaOriginal = reporte.querySelector(".tabla-reporte");
            const tablaClonada = tablaOriginal.cloneNode(true);

            contenedor = document.createElement("div");
            contenedor.className = "reporte-imagen";
            contenedor.style.position = "fixed";
            contenedor.style.left = "-100000px";
            contenedor.style.top = "0";
            contenedor.style.zIndex = "-1";
            contenedor.style.background = "#fff";
            contenedor.style.color = "#212529";
            contenedor.style.padding = "25px";
            contenedor.style.width = "max-content";

            const encabezado = document.createElement("div");
            encabezado.className = "reporte-imagen-encabezado";
            encabezado.style.marginBottom = "20px";
            encabezado.style.color = "#212529";

            const titulo = document.createElement("h3");
            titulo.textContent = "Reporte Diario de Producto Terminado";
            titulo.style.fontSize = "22px";
            titulo.style.fontWeight = "700";
            titulo.style.marginBottom = "10px";
            encabezado.appendChild(titulo);

            function agregarDato(texto) {
                const parrafo = document.createElement("p");
                parrafo.textContent = texto;
                parrafo.style.marginBottom = "4px";
                parrafo.style.fontSize = "14px";
                encabezado.appendChild(parrafo);
            }

            agregarDato("Movimiento: " + (movimiento === "entradas" ? "Entradas" : "Salidas"));
            agregarDato(data.tipo_producto === "especial"
                ? "Tienda especial: " + data.nombre_especial
                : "Tipo de producto: Normal");

            if (movimiento === "salidas") {
                agregarDato("Destino: " + nombresDestinos[destino]);
            }

            agregarDato("Fecha del reporte: " + fechaReporte);
            agregarDato("Fecha y hora de captura: " + fechaCaptura);

            if (mostrarStock.checked) {
                const leyenda = document.createElement("p");
                leyenda.textContent = "Cantidad del movimiento / Stock actual";
                leyenda.style.color = "#6c757d";
                leyenda.style.fontSize = "12px";
                encabezado.appendChild(leyenda);
            }

            // Apariencia clara independiente del tema de la página.
            tablaClonada.style.setProperty("--bs-table-bg", "#ffffff");
            tablaClonada.style.setProperty("--bs-table-color", "#212529");
            tablaClonada.style.setProperty("--bs-table-border-color", "#dee2e6");
            tablaClonada.style.setProperty("--bs-table-striped-bg", "#ffffff");
            tablaClonada.style.setProperty("--bs-table-striped-color", "#212529");
            tablaClonada.style.setProperty("--bs-table-hover-bg", "#ffffff");

            tablaClonada.querySelectorAll("th, td").forEach(celda => {
                celda.style.color = "#212529";
                celda.style.borderColor = "#dee2e6";
                celda.style.backgroundColor = "#ffffff";
            });
            tablaClonada.querySelectorAll("thead th").forEach(celda => {
                celda.style.setProperty("background-color", "#343a40", "important");
                celda.style.setProperty("color", "#ffffff", "important");
            });
            tablaClonada.querySelectorAll("tfoot td").forEach(celda => {
                celda.style.setProperty("background-color", "#e9ecef", "important");
                celda.style.setProperty("color", "#212529", "important");
            });
            tablaClonada.querySelectorAll(".col-total").forEach(celda => {
                celda.style.setProperty("background-color",
                    celda.closest("tfoot") ? "#d5e0eb" : "#e9eff5", "important");
                celda.style.setProperty("color", "#263746", "important");
            });
            tablaClonada.querySelectorAll(".cantidad-movimiento").forEach(el => {
                el.style.color = "#212529";
            });
            tablaClonada.querySelectorAll(".cantidad-stock").forEach(el => {
                el.style.color = "#858c94";
            });

            contenedor.appendChild(encabezado);
            contenedor.appendChild(tablaClonada);
            document.body.appendChild(contenedor);

            const canvas = await html2canvas(contenedor, {
                backgroundColor: "#ffffff",
                scale: 2,
                useCORS: true,
                scrollX: 0,
                scrollY: 0,
                windowWidth: Math.max(
                    document.documentElement.clientWidth,
                    contenedor.scrollWidth
                )
            });

            const fechaArchivo = ahora.getFullYear() + "-" +
                String(ahora.getMonth() + 1).padStart(2, "0") + "-" +
                String(ahora.getDate()).padStart(2, "0") + "_" +
                String(ahora.getHours()).padStart(2, "0") + "-" +
                String(ahora.getMinutes()).padStart(2, "0");

            const nombreArchivo = [
                "Reporte",
                movimiento === "entradas" ? "Entradas" : "Salidas",
                data.tipo_producto === "especial" ? data.especial : "Normal",
                movimiento === "salidas" ? destino : "General",
                data.fecha,
                fechaArchivo
            ].join("_") + ".png";

            const enlace = document.createElement("a");
            enlace.download = nombreArchivo;
            enlace.href = canvas.toDataURL("image/png");
            enlace.click();

        } catch (error) {
            console.error("Error al generar imagen:", error);
            alert("No se pudo generar la imagen del reporte.");
        } finally {
            if (contenedor) contenedor.remove();
            btnDescargarImagen.disabled = false;
            btnDescargarImagen.innerHTML = textoOriginal;
            generandoImagen = false;
        }
    }

    async function cargarReporte() {
        if (!filtroFecha.value) {
            mostrarError("Selecciona una fecha válida.");
            return;
        }

        const numeroSolicitud = ++solicitudActual;
        const movimiento = filtroMovimiento.value;
        const destino = filtroDestino.value;
        const fecha = filtroFecha.value;
        const tipoProducto = filtroTipoProducto.value;
        const especial = filtroEspecial.value;

        const parametros = new URLSearchParams({
            fecha: fecha,
            movimiento: movimiento,
            destino: destino,
            tipo_producto: tipoProducto,
            especial: especial
        });

        indicadorCarga.classList.remove("d-none");
        btnConsultar.disabled = true;
        btnDescargarImagen.disabled = true;
        datosReporteActual = null;

        try {
            const respuesta = await fetch(`${urlDatos}?${parametros.toString()}`);
            if (!respuesta.ok) throw new Error("No se pudo consultar el reporte.");
            const data = await respuesta.json();
            if (numeroSolicitud !== solicitudActual) return;

            tituloReporte.textContent = movimiento === "entradas"
                ? "Reporte de Entradas" : "Reporte de Salidas";

            const fechaFormateada = fecha.split("-").reverse().join("/");
            const nombreTipo = data.tipo_producto === "especial"
                ? `Especial: ${data.nombre_especial}` : "Productos normales";

            subtituloReporte.textContent = movimiento === "entradas"
                ? `Fecha: ${fechaFormateada} | ${nombreTipo}`
                : `Fecha: ${fechaFormateada} | ${nombreTipo} | Destino: ${nombresDestinos[destino]}`;

            datosReporteActual = data;
            renderizarTabla(data);

        } catch (error) {
            if (numeroSolicitud !== solicitudActual) return;
            mostrarError(error.message);
        } finally {
            if (numeroSolicitud === solicitudActual) {
                indicadorCarga.classList.add("d-none");
                btnConsultar.disabled = false;
                btnDescargarImagen.disabled = generandoImagen;
            }
        }
    }

    filtroMovimiento.addEventListener("change", function () {
        actualizarFiltros();
        cargarReporte();
    });
    filtroTipoProducto.addEventListener("change", function () {
        actualizarFiltros();
        cargarReporte();
    });
    filtroEspecial.addEventListener("change", cargarReporte);
    filtroDestino.addEventListener("change", cargarReporte);
    filtroFecha.addEventListener("change", cargarReporte);
    btnConsultar.addEventListener("click", cargarReporte);

    mostrarStock.addEventListener("change", function () {
        if (datosReporteActual) renderizarTabla(datosReporteActual);
    });

    btnDescargarImagen.addEventListener("click", descargarImagenReporte);
    actualizarFiltros();
    cargarReporte();
});
