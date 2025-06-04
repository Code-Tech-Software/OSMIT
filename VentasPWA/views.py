from rest_framework import viewsets
from Usuario.models import Usuario
from ProductoTerminado.models import ProductoTerminado, Vehiculo, Ruta, Cliente, PresentacionProductoTerminado, \
    GramajeProductoTerminado, ClienteDiasVisita
from VentasPWA.serializers import ProductoTerminadoSerializer, VehiculoSerializer, RutaSerializer, UsuarioSerializer, \
    ClienteSerializer, PresentacionProductoTerminadoSerializer, GramajeProductoTerminadoSerializer, \
    ClienteDiasVisitaSerializer,  VentaClienteSerializer


#PRODUCTO
class ProductoTerminadoViewSet(viewsets.ModelViewSet):
    queryset = ProductoTerminado.objects.filter(estado=True)
    serializer_class = ProductoTerminadoSerializer

#VEHICULO
class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.filter(estado=True)
    serializer_class = VehiculoSerializer


#RUTA
class RutaViewSet(viewsets.ModelViewSet):
    queryset = Ruta.objects.filter(estado=True)
    serializer_class = RutaSerializer

#USUARIO
class UsuarioViewSet(viewsets.ModelViewSet):  # Usa ModelViewSet si quieres soporte completo (GET, POST, PUT, DELETE)
    queryset = Usuario.objects.filter(is_active=True)
    serializer_class = UsuarioSerializer

#CLIENTE
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.filter(estado=True)
    serializer_class = ClienteSerializer

#PresentacionProductoTerminado
class PresentacionProductoTerminadoViewSet(viewsets.ModelViewSet):
    queryset = PresentacionProductoTerminado.objects.filter(estado=True)
    serializer_class = PresentacionProductoTerminadoSerializer

#GramajeProductoTerminado
class GramajeProductoTerminadoViewSet(viewsets.ModelViewSet):
    queryset = GramajeProductoTerminado.objects.filter(estado=True)
    serializer_class = GramajeProductoTerminadoSerializer

#ClienteDiasVisita
class ClienteDiasVisitaViewSet(viewsets.ModelViewSet):
    queryset = ClienteDiasVisita.objects.all()
    serializer_class = ClienteDiasVisitaSerializer\




#En revision

#VentaCliente
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class EnviarVentaAPIView(APIView):
    def post(self, request):
        serializer = VentaClienteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)