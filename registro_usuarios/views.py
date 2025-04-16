from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from autenticacion.models import CustomUser
from .serializer import RegistroUSerializer

class RegistroUViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = RegistroUSerializer

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Endpoint para cambiar el estado (activo/inactivo) del usuario.
        Se espera recibir un JSON con {'is_active': true/false}.
        """
        usuario = self.get_object()
        nuevo_estado = request.data.get('is_active')
        if nuevo_estado is None:
            return Response({"error": "Se requiere el campo 'is_active'."}, status=status.HTTP_400_BAD_REQUEST)
        usuario.is_active = nuevo_estado
        usuario.username = request.data.get('username', usuario.nombre)  # Actualiza el username si se proporciona
        usuario.save()
        return Response({"status": "Estado actualizado", "is_active": usuario.is_active})
    