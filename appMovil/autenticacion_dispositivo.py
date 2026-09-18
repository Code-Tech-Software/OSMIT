from django.contrib.auth.hashers import check_password
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission

from .models import Dispositivo


def validar_dispositivo(request):
    codigo = request.headers.get("X-Dispositivo")
    credencial = request.headers.get("X-Credencial")

    if not codigo or not credencial:
        return Response(
            {
                "success": False,
                "message": "Credenciales de dispositivo requeridas."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        dispositivo = Dispositivo.objects.get(codigo=codigo)
    except Dispositivo.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Dispositivo no encontrado."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if not dispositivo.activo:
        return Response(
            {
                "success": False,
                "message": "El dispositivo se encuentra inactivo."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    if not check_password(credencial, dispositivo.credencial_hash):
        return Response(
            {
                "success": False,
                "message": "Credencial incorrecta."
            },
            status=status.HTTP_401_UNAUTHORIZED
        )

    return None


class DispositivoActivoPermission(BasePermission):

    message = "Dispositivo no autorizado."

    def has_permission(self, request, view):

        codigo = request.headers.get("X-Dispositivo")
        credencial = request.headers.get("X-Credencial")

        if not codigo or not credencial:
            self.message = "Credenciales de dispositivo requeridas."
            return False

        try:
            dispositivo = Dispositivo.objects.get(codigo=codigo)
        except Dispositivo.DoesNotExist:
            self.message = "Dispositivo no encontrado."
            return False

        if not dispositivo.activo:
            self.message = "El dispositivo se encuentra inactivo."
            return False

        if not check_password(
            credencial,
            dispositivo.credencial_hash
        ):
            self.message = "Credencial incorrecta."
            return False

        request.dispositivo = dispositivo

        return True