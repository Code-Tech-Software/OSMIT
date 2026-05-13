from django.db import models

from ProductoTerminado.models import Ruta, Vehiculo, ProductoVariacion, Cliente
from Usuario.models import Usuario



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
    TIPO_VENTA_CHOICES = [
        ('CONTADO', 'Contado'),
        ('CREDITO', 'Crédito'),
    ]

    ESTADO_PAGO_CHOICES = [
        ('PAGADO', 'Pagado'),
        ('PENDIENTE', 'Pendiente'),
        ('PARCIAL', 'Pago Parcial'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    #Aqui falta el usuario
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Nuevos campos para crédito:
    tipo_venta = models.CharField(max_length=10, choices=TIPO_VENTA_CHOICES, default='CONTADO')
    estado_pago = models.CharField(max_length=10, choices=ESTADO_PAGO_CHOICES, default='PAGADO')
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_vencimiento = models.DateField(null=True, blank=True)  # Cuándo debe pagar esta nota


    sincronizado = models.BooleanField(default=False)

    def __str__(self):
        cliente_nombre = self.cliente.nombre if self.cliente else "Cliente general"
        return f"Venta - {cliente_nombre} - {self.fecha}"


class Abono(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='abonos')
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, help_text="Quién cobró el abono")
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abono de ${self.monto} a Venta {self.venta.id} por {self.usuario}"



class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)
    # aqui falta el puto campo de nombre producto
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
    

class Devolucion(models.Model):
    tipo = models.CharField(max_length=50)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    mini_bodega = models.ForeignKey(MiniBodega, on_delete=models.CASCADE)
    fecha = models.DateTimeField()
    descripcion = models.TextField()
    sincronizado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class DevolucionDetalle(models.Model):
    devolucion = models.ForeignKey(Devolucion, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class MiniBodegaDetalleMerma(models.Model):
    mini_bodega = models.ForeignKey(MiniBodega, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    devolucion = models.ForeignKey('Devolucion', on_delete=models.CASCADE, null=True, blank=True)
