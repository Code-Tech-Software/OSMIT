from rest_framework import serializers
from django.contrib.auth import get_user_model
Usuario = get_user_model()
from ProductoTerminado.models import Vehiculo, ProductoTerminado, Ruta, Cliente, PresentacionProductoTerminado, \
    GramajeProductoTerminado, ClienteDiasVisita, VentaCliente, DetalleVentaCliente


#Producto
class ProductoTerminadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoTerminado
        fields = '__all__'

#Vehiculo
class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = '__all__'

#Ruta
class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = '__all__'


#Cliente
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'


#Usuarios
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        exclude = ['groups', 'user_permissions']


#PresentacionProductoTerminado
class PresentacionProductoTerminadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresentacionProductoTerminado
        fields = '__all__'


#GramajeProductoTerminado
class GramajeProductoTerminadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GramajeProductoTerminado
        fields = '__all__'



#ClienteDiasVisita
class ClienteDiasVisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClienteDiasVisita
        fields = '__all__'


#VentaCliente

class DetalleVentaClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleVentaCliente
        exclude = ['venta_cliente']

class VentaClienteSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaClienteSerializer(many=True)

    class Meta:
        model = VentaCliente
        fields = ['fecha_venta', 'usuario', 'cliente', 'estado', 'detalles']

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        venta = VentaCliente.objects.create(**validated_data)
        for detalle in detalles_data:
            DetalleVentaCliente.objects.create(venta_cliente=venta, **detalle)
        return venta
