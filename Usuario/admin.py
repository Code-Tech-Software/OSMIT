from django.contrib import admin

from Usuario.models import *

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Turno)
admin.site.register(TurnoUsuario)


