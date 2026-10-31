document.addEventListener('DOMContentLoaded', function () {
  if (!window.jQuery || !jQuery.fn.DataTable) return;
  const tablas = ['tabla-ventas-resumen', 'tabla-abonos-resumen', 'tabla-devoluciones-resumen', 'tabla-rotaciones-resumen'];
  tablas.forEach(function (id) {
    if (jQuery.fn.DataTable.isDataTable('#' + id)) return;
    jQuery('#' + id).DataTable({pageLength:25, order:[[0,'desc']], autoWidth:false, language:{emptyTable:'No hay movimientos para los filtros seleccionados', zeroRecords:'No se encontraron resultados', search:'Buscar:', lengthMenu:'Mostrar _MENU_ registros', info:'Mostrando _START_ a _END_ de _TOTAL_ registros', infoEmpty:'Sin registros', infoFiltered:'(filtrados de _MAX_)', paginate:{first:'Primero', last:'Último', next:'Siguiente', previous:'Anterior'}}});
  });
});