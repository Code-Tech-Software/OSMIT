
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from ProductoGranel.models import CategoriaProducto

class PresentacionProductoTerminado(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField( blank=True, null=True)
    imagen = models.ImageField(upload_to='fotos_presentacionProductoTerminado/', blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class GramajeProductoTerminado(models.Model):
    nombre = models.CharField(max_length=255)
    imagen = models.ImageField(upload_to='fotos_gramajeProductoTerminado/', blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    marca = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    placa = models.CharField(max_length=255)
    kilometraje = models.DecimalField(max_digits=10, decimal_places=2)
    ultimo_servicio = models.DateField () #SOLO PARA LA FECHA
    observaciones = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='fotos_vehiculos/', blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.placa}  - {self.marca}"

class Ruta(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    nombre_negocio = models.CharField(max_length=255)
    giro = models.CharField(max_length=255,null=True, blank=True)
    tipo_exhibidor = models.CharField(max_length=255,null=True, blank=True)
    direccion = models.CharField(max_length=255)
    localidad = models.CharField(max_length=255,null=True, blank=True)
    colonia = models.CharField(max_length=255,null=True, blank=True)
    telefono = models.CharField(max_length=50,null=True, blank=True)
    credito = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    imagen = models.ImageField(upload_to='fotos_cliente/', blank=True, null=True)
    observaciones = models.TextField(null=True, blank=True)
    ruta = models.ForeignKey(Ruta, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class ClienteDiasVisita(models.Model):
    DIAS = (
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miercoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sabado'),
        ('domingo', 'Domingo'),
    )

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    dia_semana = models.CharField(max_length=255, choices=DIAS)

    def __str__(self):
        return self.dia_semana



class ProductoTerminado(models.Model):
    nombre = models.CharField(max_length=255)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria_producto = models.ForeignKey(CategoriaProducto, on_delete=models.CASCADE)
    stock = models.DecimalField(max_digits=10, decimal_places=2)
    stock_min = models.DecimalField(max_digits=10, decimal_places=2)
    presentacion_producto_terminado = models.ForeignKey(PresentacionProductoTerminado, on_delete=models.CASCADE)
    gramaje_producto_terminado = models.ForeignKey(GramajeProductoTerminado, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='fotos_productoTerminado/', blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class VentaCliente(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
    )

    fecha_venta = models.DateTimeField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default="pendiente")
    stock_descontado = models.BooleanField(default=False, help_text="¿Se ha restado ya el stock para esta venta?")

    def __str__(self):
        return f"Venta {self.id} a {self.cliente.nombre}"

class DetalleVentaCliente(models.Model):
    venta_cliente = models.ForeignKey(VentaCliente, on_delete=models.CASCADE)
    producto_terminado = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio actual del producto")

    def __str__(self):
        return f"Detalle de Venta {self.venta_cliente.id}"





class ConcentradoPedidos(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('procesado', 'Procesado')
    )

    ruta = models.ForeignKey(Ruta, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_concentrado = models.DateTimeField()
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default="pendiente")

    def __str__(self):
        return f"Concentrado {self.id}"

class DetalleConcentradoPedidos(models.Model):
    concentrado_pedidos = models.ForeignKey(ConcentradoPedidos, on_delete=models.CASCADE)
    producto_terminado = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    cantidad_total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Suma de los pedidos de los clientes")

    def __str__(self):
        return f"Detalle Concentrado {self.concentrado_pedidos.id}"



class InventarioRuta(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    producto_terminado = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    stock = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Inventario Ruta {self.ruta.nombre} - {self.producto_terminado.nombre}"






class SalidaPTerminado(models.Model):
    DESTINO_CHOICES = (
        ('opcion1', 'Ruta'),
        ('opcion2', 'Mitsu'),
        ('opcion3', 'Maestro'),
        ('opcion4', 'Otros'),
    )
    fecha_salida = models.DateTimeField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    ruta = models.ForeignKey(Ruta, on_delete=models.SET_NULL, null=True, blank=True)

    destino = models.CharField(max_length=255, choices=DESTINO_CHOICES,default="opcion1")
    nota = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Salida {self.id}"

class DetalleSalidaPTerminado(models.Model):
    salida_p_terminado = models.ForeignKey(SalidaPTerminado, on_delete=models.CASCADE)
    producto_terminado = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Salida {self.salida_p_terminado.id}"



class EntradaPTerminado(models.Model):
    fecha_entrada = models.DateTimeField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.TextField()

    def __str__(self):
        return f"Entrada {self.id}"

class DetalleEntradaPTerminado(models.Model):

    entrada_p_terminado = models.ForeignKey(EntradaPTerminado, on_delete=models.CASCADE)
    producto_terminado = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Entrada {self.entrada_p_terminado.id}"

class CorteInventarioPTerminado(models.Model):
    fecha = models.DateTimeField(help_text="Fecha del corte")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, help_text="Quién realizó el corte")
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=[('pendiente', 'Pendiente'), ('correcto', 'Correcto'), ('ajustado', 'Ajustado')], default='correcto')

    def __str__(self):
        return f"Corte Inventario {self.id}"

class DetalleCorteInventarioPTerminado(models.Model):
    corte_inventario_p_terminado = models.ForeignKey(CorteInventarioPTerminado, on_delete=models.CASCADE)
    producto_terminado = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE)
    stock_teorico = models.DecimalField(max_digits=10, decimal_places=2, help_text="Según las salidas/entradas")
    stock_real = models.DecimalField(max_digits=10, decimal_places=2, help_text="Lo contado físicamente")
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, help_text="stock_real - stock_teorico")
    ajuste_necesario = models.BooleanField(default=False, help_text="Si se requiere un ajuste en la BD")

    def __str__(self):
        return f"Detalle Corte {self.corte_inventario_p_terminado.id}"

