from django.db import models

from ProductoTerminado.models import Ruta, Vehiculo, ProductoVariacion, Cliente
from Usuario.models import Usuario



# Hubo unos cambios en ventas, en la app despues cambiar aqui
# Si en un futuro se mete ventas a la app, tendre que agregar updated_at = models.DateTimeField(auto_now=True)


class MiniBodega(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    fecha = models.DateField()
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)

    estado = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MiniBodega - {self.ruta.nombre} - {self.fecha}"

class MiniBodegaDetalle(models.Model):
    mini_bodega = models.ForeignKey(MiniBodega, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)

    cantidad_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_actual = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Detalle - {self.mini_bodega} - {self.producto_variacion}"



class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    sincronizado = models.BooleanField(default=False)

    def __str__(self):
        cliente_nombre = self.cliente.nombre if self.cliente else "Cliente general"
        return f"Venta - {cliente_nombre} - {self.fecha}"


class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)

    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle - {self.venta} - {self.producto_variacion}"


class PedidoReabastecimiento(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    estado = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Pedido - {self.ruta.nombre} - {self.fecha}"


class PedidoReabastecimientoDetalle(models.Model):
    pedido = models.ForeignKey(PedidoReabastecimiento, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)

    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Detalle - {self.pedido} - {self.producto_variacion}"