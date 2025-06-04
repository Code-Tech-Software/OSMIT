from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from Usuario.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('Usuario.urls')),
    path('granel/', include('ProductoGranel.urls')),

    path('terminado/', include('ProductoTerminado.urls')),

    path('vehiculosRutas/', include('VehiculosRutas.urls')),

    path('', dashboard, name='dashboard'),
    # Redirigir la raíz al dashboard # IMPORTANTE ES DONDE EMPIEZA LA APLICACION#

    path('ventasPWA/', include('VentasPWA.urls')),

]
# Para servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
