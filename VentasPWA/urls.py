from rest_framework import routers

from VentasPWA.views import ProductoTerminadoViewSet, VehiculoViewSet, RutaViewSet, UsuarioViewSet, ClienteViewSet, \
    PresentacionProductoTerminadoViewSet, GramajeProductoTerminadoViewSet, \
    ClienteDiasVisitaViewSet

from django.urls import path
from .views import EnviarVentaAPIView

urlpatterns = [
    path('api/venta/', EnviarVentaAPIView.as_view(), name='enviar_venta'),
]

router = routers.DefaultRouter()
router.register(r'productoTerminado', ProductoTerminadoViewSet)

router.register(r'vehiculo', VehiculoViewSet)

router.register(r'ruta', RutaViewSet)

router.register(r'usuario', UsuarioViewSet)


router.register(r'cliente', ClienteViewSet)

router.register(r'presentacionProductoTerminado', PresentacionProductoTerminadoViewSet)

router.register(r'gramajeProductoTerminado', GramajeProductoTerminadoViewSet)

#ClienteDiasVisita
router.register(r'clienteDiasVisita', ClienteDiasVisitaViewSet)



urlpatterns += router.urls
