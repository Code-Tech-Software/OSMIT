from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class CategoriaProducto(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='fotos_categoriaProductos/', blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20,blank=True, null=True)
    correo = models.EmailField(unique=True,blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class ProductoGranel(models.Model):
    nombre = models.CharField(max_length=255)
    categoria_producto = models.ForeignKey(CategoriaProducto, on_delete=models.CASCADE)
    stock = models.DecimalField(max_digits=10, decimal_places=2)
    stock_min = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_medida = models.CharField(max_length=50)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    tiempo_caducidad = models.PositiveIntegerField() # Días
    imagen = models.ImageField(upload_to='fotos_productoGranel/', blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class EntradaGranel(models.Model):
    fecha_entrada = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Entrada {self.id} - {self.fecha_entrada}"

class DetalleEntradaGranel(models.Model):
    entrada_granel = models.ForeignKey(EntradaGranel, on_delete=models.CASCADE)
    producto_granel = models.ForeignKey(ProductoGranel, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Entrada {self.id} - Producto: {self.producto_granel.nombre}"

class SalidaGranel(models.Model):
    fecha_salida = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    destino = models.CharField(max_length=255)
    nota = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Salida {self.id} - {self.fecha_salida}"

class DetalleSalidaGranel(models.Model):
    salida_granel = models.ForeignKey(SalidaGranel, on_delete=models.CASCADE)
    producto_granel = models.ForeignKey(ProductoGranel, on_delete=models.CASCADE)
    lote = models.ForeignKey('Lote', on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Salida {self.id} - Producto: {self.producto_granel.nombre}"

class PedidoProduccion(models.Model):
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.TextField(blank=True, null=True)
    procesado = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=[('pendiente', 'Pendiente'), ('en_produccion', 'En Producción'), ('finalizado', 'Finalizado'),('rechazado', 'Rechazado')], default='pendiente')

    def __str__(self):
        return f"Pedido {self.id} - Estado: {self.estado}"

class DetallePedidoProduccion(models.Model):
    pedido_produccion = models.ForeignKey(PedidoProduccion, on_delete=models.CASCADE)
    producto_granel = models.ForeignKey(ProductoGranel, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Pedido {self.id} - Producto: {self.producto_granel.nombre}"

class DevolucionGranel(models.Model):
    fecha_devolucion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    salida_granel = models.ForeignKey(SalidaGranel, on_delete=models.CASCADE)
    nota = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Devolución {self.id} - {self.fecha_devolucion}"

class DetalleDevolucionGranel(models.Model):
    devolucion_granel = models.ForeignKey(DevolucionGranel, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    producto_granel = models.ForeignKey(ProductoGranel, on_delete=models.CASCADE)
    lote = models.ForeignKey('Lote', on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Devolución {self.id} - Producto: {self.producto_granel.nombre}"

class Lote(models.Model):
    producto_granel = models.ForeignKey(ProductoGranel, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_entrada = models.DateTimeField()
    fecha_caducidad = models.DateField()
    estado = models.BooleanField(default=True)
    estado_lote = models.CharField(max_length=20, choices=[('activo', 'Activo'), ('agotado', 'Agotado'), ('caducado', 'Caducado')], default='activo')

    def __str__(self):
        return f"Lote {self.id} - Estado: {self.estado_lote}"

class CorteInventarioGranel(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[('pendiente', 'Pendiente'), ('correcto', 'Correcto'), ('ajustado', 'Ajustado')], default='correcto')

    def __str__(self):
        return f"Corte Inventario {self.id} - Estado: {self.estado}"

class DetalleCorteInventarioGranel(models.Model):
    corte_inventario = models.ForeignKey(CorteInventarioGranel, on_delete=models.CASCADE)
    producto_granel = models.ForeignKey(ProductoGranel, on_delete=models.CASCADE)
    stock_teorico = models.DecimalField(max_digits=10, decimal_places=2)
    stock_real = models.DecimalField(max_digits=10, decimal_places=2)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2)
    ajuste_necesario = models.BooleanField(default=False)

    def __str__(self):
        return f"Detalle Corte {self.id} - Producto: {self.producto_granel.nombre}"
