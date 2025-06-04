from django.urls import path
from .views import registro, iniciar_sesion, cerrar_sesion, dashboard, ver_perfil, editar_perfil, cambiar_contrasena, \
    listar_turnos, asignar_turno, eliminar_turno, listar_roles, agregar_rol, editar_rol, eliminar_rol, crear_turno, \
    editar_turno, turnos_asignados, gestionar_usuarios, eliminar_turno_usuario, editar_turno_usuario

urlpatterns = [
    path('registro/', registro, name='registro'),
    path('login/', iniciar_sesion, name='login'),
    path('logout/', cerrar_sesion, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),

    path('perfil/', ver_perfil, name='ver_perfil'),
    path('perfil/editar/', editar_perfil, name='editar_perfil'),
    path('perfil/cambiar_contrasena/', cambiar_contrasena, name='cambiar_contrasena'),


    # pulina
    # Otras rutas...
    path('roles/', listar_roles, name='listar_roles'),
    path('roles/agregar/', agregar_rol, name='agregar_rol'),
    path('roles/editar/<int:rol_id>/', editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:rol_id>/', eliminar_rol, name='eliminar_rol'),

    # Rutas de Turnos
    path('turnos/', listar_turnos, name='listar_turnos'),
    path('turnos/crear/', crear_turno, name='crear_turno'),
    path('turnos/editar/<int:turno_id>/', editar_turno, name='editar_turno'),
    path('turnos/eliminar/<int:turno_id>/', eliminar_turno, name='eliminar_turno'),

    # Rutas de Asignación de Turnos
    path('turnos/asignar/', asignar_turno, name='asignar_turno'),
    path('turno/eliminarAsigancion/<int:pk>/', eliminar_turno_usuario, name='eliminar_turno_usuario'),
    path('turno/editarAsigancion/<int:pk>/', editar_turno_usuario, name='editar_turno_usuario'),
    path('turnos/asignados/', turnos_asignados, name='turnos_asignados'),
    path('usuarios/', gestionar_usuarios, name='gestionar_usuarios'),




]