from rest_framework import serializers

from ProductoGranel.models import CategoriaProducto
from ProductoTerminado.models import PresentacionProductoTerminado, ProductoTerminado, ClienteDiasVisita
from Usuario.models import Rol
from .models import *

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'


class CategoriaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProducto
        fields = '__all__'


class PresentacionProductoTerminadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresentacionProductoTerminado
        fields = '__all__'


class ProductoTerminadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoTerminado
        fields = '__all__'


class ProductoVariacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoVariacion
        fields = '__all__'


class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = '__all__'


class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = '__all__'


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'


class ClienteDiasVisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClienteDiasVisita
        fields = '__all__'

class MiniBodegaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiniBodega
        fields = '__all__'


class MiniBodegaDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiniBodegaDetalle
        fields = '__all__'

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = '__all__'


class VentaDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VentaDetalle
        fields = '__all__'


class PedidoReabastecimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PedidoReabastecimiento
        fields = '__all__'


class PedidoReabastecimientoDetalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PedidoReabastecimientoDetalle
        fields = '__all__'



##Cosas de del reabastecimiento y mini bodega, no se si dejarlas aqui o hacer otro archivo serializers_personalizados.py o algo asi

class MiniBodegaDetalleSerializer2(serializers.Serializer):
    producto_variacion_id = serializers.IntegerField()
    cantidad_actual = serializers.DecimalField(max_digits=10, decimal_places=2)

class CerrarMiniBodegaSerializer2(serializers.Serializer):
    mini_bodega_id = serializers.IntegerField()
    productos = MiniBodegaDetalleSerializer2(many=True)

class PedidoDetalleSerializer(serializers.Serializer):
    producto_variacion_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=10, decimal_places=2)

class CrearPedidoReabastecimientoSerializer(serializers.Serializer):
    ruta_id = serializers.IntegerField()
    productos = PedidoDetalleSerializer(many=True)