
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from ProductoGranel.models import CategoriaProducto

class PresentacionProductoTerminado(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField( blank=True, null=True)
    imagen = models.ImageField(upload_to='fotos_presentacionProductoTerminado/', blank=True, null=True)
    estado = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


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
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.placa}  - {self.marca}"

class Ruta(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    limite_credito = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,help_text="Monto máximo que se le puede fiar")
    saldo_adeudo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,help_text="Cuánto debe el cliente actualmente")

    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    imagen = models.ImageField(upload_to='fotos_cliente/', blank=True, null=True)
    observaciones = models.TextField(null=True, blank=True)
    ruta = models.ForeignKey(Ruta, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dia_semana

class ProductoTerminado(models.Model):
    nombre = models.CharField(max_length=255)
    categoria_producto = models.ForeignKey(CategoriaProducto, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='fotos_productoTerminado/', blank=True, null=True)
    estado = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class ProductoVariacion(models.Model):
    producto = models.ForeignKey(ProductoTerminado, on_delete=models.CASCADE, related_name="variaciones")
    presentacion = models.ForeignKey(PresentacionProductoTerminado, on_delete=models.CASCADE)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.DecimalField(max_digits=10, decimal_places=2)
    stock_min = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_barras = models.CharField(max_length=50,null=True,blank=True,unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.producto.nombre} - {self.presentacion} "




class EntradaPTerminado(models.Model):
    fecha_entrada = models.DateTimeField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nota = models.TextField()

    def __str__(self):
        return f"Entrada {self.id}"

class DetalleEntradaPTerminado(models.Model):
    entrada_p_terminado = models.ForeignKey(EntradaPTerminado, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Entrada {self.entrada_p_terminado.id}"



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
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Salida {self.salida_p_terminado.id}"


class InventarioRuta(models.Model):
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    producto_variacion = models.ForeignKey(ProductoVariacion, on_delete=models.CASCADE)
    stock = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Inventario Ruta {self.ruta.nombre} - {self.producto_variacion}"







