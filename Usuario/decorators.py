from functools import wraps
from django.core.exceptions import PermissionDenied



def requiere_roles(*roles_permitidos):
    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request,*args,**kwargs):
            usuario=request.user

            #Administrador tiene acceso a todo

            if usuario.rol and usuario.rol.nombre=="Administrador":
                return view_func(request,*args,**kwargs)


            #Comprobar si el rol del usuario esta permitido
            if usuario.rol and usuario.rol.nombre in roles_permitidos:
                return view_func(request,*args,**kwargs)

            raise PermissionDenied
        return wrapper
    return decorador


def solo_administrador(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.rol and request.user.rol.nombre == "Administrador":
            return view_func(request, *args, **kwargs)

        raise PermissionDenied

    return wrapper
    
