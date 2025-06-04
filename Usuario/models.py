from django.contrib.auth.models import AbstractUser
from django.db import models

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)  # Eliminación lógica

    def __str__(self):
        return self.nombre

    @staticmethod
    def activos():
        """ Devuelve solo los roles activos. """
        return Rol.objects.filter(estado=True)


class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15,blank=True, null=True)
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True)
    direccion = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)


    def __str__(self):
        return self.first_name + " " + self.last_name

class Turno(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)  # Eliminación lógica

    def __str__(self):
        return self.nombre

    @staticmethod
    def activos():
        """ Devuelve solo los turnos activos. """
        return Turno.objects.filter(estado=True)


class TurnoUsuario(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.BooleanField(default=True)  # Eliminación lógica

    def __str__(self):
        return f"{self.usuario.username} - {self.turno.nombre} ({self.fecha_inicio} - {self.fecha_fin})"

    @staticmethod
    def activos():
        """ Devuelve solo los turnos activos. """
        return TurnoUsuario.objects.filter(estado=True)