from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import RegistroForm, LoginForm, EditarPerfilForm, TurnoUsuarioForm, RolForm, TurnoForm, \
    CustomPasswordChangeForm, TurnoUsuarioFormEditar
from .models import Usuario, TurnoUsuario, Rol, Turno
from django.contrib import messages

@login_required
def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, "Usuario agregado correctamente.")
            return redirect('gestionar_usuarios')
        else:
            # Agrega errores personalizados con Notyf
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label if field in form.fields else field}: {error}")
    else:
        form = RegistroForm()

    return render(request, 'Usuario/registro.html', {'form': form})

def iniciar_sesion(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            return redirect('dashboard')
        else:
            form.errors.pop('__all__', None)  # Remueve el mensaje de Django
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()
    return render(request, 'Usuario/login.html', {'form': form})
@login_required
def dashboard(request):
    return render(request, 'Usuario/dashboard.html')
@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect('login')
@login_required
def ver_perfil(request):
    return render(request, 'Usuario/perfil.html')
@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado exitosamente.")  # esto para las notificaciones
            return redirect('ver_perfil')

    else:
        form = EditarPerfilForm(instance=request.user)
    return render(request, 'Usuario/editar_perfil.html', {'form': form})
@login_required
def cambiar_contrasena(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Contraseña actualizada.")  # esto para las notificaciones
            return redirect('ver_perfil')
        else:
            for field in form.errors:
                for error in form.errors[field]:
                    if "muy corta" in error or "too short" in error:
                        messages.error(request, "Usa al menos 3 caracteres.")  # <- Aquí la personalizas
                    elif field == 'old_password':
                        messages.error(request, "La contraseña actual ingresada es incorrecta.")
                    elif "no coinciden" in error or "do not match" in error:
                        messages.error(request, "Las contraseñas nuevas no coinciden.")
                    else:
                        messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'Usuario/cambiar_contrasena.html', {'form': form})

@login_required
def listar_roles(request):
    mostrar_todos = request.GET.get('mostrar_todos') == '1'

    if mostrar_todos:
        roles = Rol.objects.all()
    else:
        roles = Rol.objects.filter(estado=True)

    return render(request, 'Usuario/roles/listar_roles.html', {
        'roles': roles,
        'mostrar_todos': mostrar_todos
    })

@login_required
def agregar_rol(request):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Rol agregado.")  # esto para las notificaciones
            return redirect('listar_roles')
    else:
        form = RolForm()
    return render(request, 'Usuario/roles/agregar_rol.html', {'form': form})

@login_required
def editar_rol(request, rol_id):
    rol = get_object_or_404(Rol, id=rol_id)
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            messages.success(request, "Rol actualizado.")  # esto para las notificaciones
            return redirect('listar_roles')
    else:
        form = RolForm(instance=rol)
    return render(request, 'Usuario/roles/editar_rol.html', {'form': form})

@login_required
def eliminar_rol(request, rol_id):
    rol = get_object_or_404(Rol, id=rol_id)

    # Verificar si el rol tiene usuarios asignados
    if Usuario.objects.filter(rol=rol).exists():
        messages.error(request, "No se puede desactivar el rol porque tiene usuarios asignados.")
    else:
        rol.estado = False  # Eliminación lógica
        rol.save()
        messages.success(request, "Rol desactivado correctamente.")

    return redirect('listar_roles')

# LISTAR TURNOS
@login_required
def listar_turnos(request):
    mostrar_todos = request.GET.get('mostrar_todos') == '1'
    if mostrar_todos:
        turnos = Turno.objects.all()
    else:
        turnos = Turno.objects.filter(estado=True)

    return render(request, 'Usuario/turnos/listar_turnos.html', {'turnos': turnos, 'mostrar_todos': mostrar_todos})

# CREAR TURNOS
@login_required
def crear_turno(request):
    if request.method == 'POST':
        form = TurnoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Turno creado correctamente.")
            return redirect('listar_turnos')
    else:
        form = TurnoForm()
    return render(request, 'Usuario/turnos/crear_turno.html', {'form': form})

# EDITAR TURNOS
@login_required
def editar_turno(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    if request.method == 'POST':
        form = TurnoForm(request.POST, instance=turno)
        if form.is_valid():
            form.save()
            messages.success(request, "Turno actualizado.")
            return redirect('listar_turnos')
    else:
        form = TurnoForm(instance=turno)
    return render(request, 'Usuario/turnos/editar_turno.html', {'form': form})


# ELIMINAR (LÓGICO) TURNOS
@login_required
def eliminar_turno(request, turno_id):
    turno = get_object_or_404(Turno, id=turno_id)
    turno.estado = False
    turno.save()
    messages.success(request, "Turno desactivado correctamente.")
    return redirect('listar_turnos')

# TURNOS A USUARIOS
@login_required
def asignar_turno(request):
    if request.method == 'POST':
        form = TurnoUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Turno asignado correctamente.")
            return redirect('turnos_asignados')
    else:
        form = TurnoUsuarioForm()
    return render(request, 'Usuario/turnos/asignar_turno.html', {'form': form})


@login_required
def turnos_asignados(request):
    turnos_usuario = TurnoUsuario.objects.all()
    return render(request, 'Usuario/turnos/turnos_asignados.html', {'turnos_usuario': turnos_usuario})

@login_required
def eliminar_turno_usuario(request, pk):
    turno_usuario = get_object_or_404(TurnoUsuario, pk=pk)
    turno_usuario.delete()
    messages.success(request, "Turno eliminado correctamente.")
    return redirect('turnos_asignados')


@login_required
def editar_turno_usuario(request, pk):
    turno_usuario = get_object_or_404(TurnoUsuario, pk=pk)
    if request.method == 'POST':
        form = TurnoUsuarioFormEditar(request.POST, instance=turno_usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Turno actualizado correctamente.")
            return redirect('turnos_asignados')
    else:
        form = TurnoUsuarioFormEditar(instance=turno_usuario)
    return render(request, 'Usuario/turnos/editar_turno_usuario.html', {'form': form})


# gestion de  USUARIOS

@login_required
def gestionar_usuarios(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        nuevo_rol_id = request.POST.get('rol_id')
        usuario = get_object_or_404(Usuario, id=usuario_id)

        # Prevenir que el usuario actual se desactive a sí mismo
        if 'toggle_estado' in request.POST:
            if usuario == request.user:
                # Mensaje de error si intentan desactivarse a sí mismos
                messages.error(request, "No puedes desactivarte a ti mismo mientras estás logueado.")
            else:
                usuario.is_active = not usuario.is_active
                usuario.save()
                messages.success(request, "Usuario Activado correctamente.")

        # Cambiar rol si se seleccionó uno
        if nuevo_rol_id:
            nuevo_rol = get_object_or_404(Rol, id=nuevo_rol_id)
            usuario.rol = nuevo_rol
            usuario.save()
            messages.success(request, "Rol actualizado.")

        return redirect('gestionar_usuarios')

    usuarios = Usuario.objects.all()
    roles = Rol.activos()
    return render(request, 'Usuario/gestionar_usuarios.html', {'usuarios': usuarios, 'roles': roles})
