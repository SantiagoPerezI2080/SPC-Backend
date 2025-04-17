from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class LoginView(APIView):
    """
    Endpoint de Login: recibe 'correo' y 'password'. Si son correctos,
    devuelve el token y datos básicos del usuario.
    """
    def post(self, request, format=None):
        correo = request.data.get("correo", "").lower()
        password = request.data.get("password")
        User = get_user_model()
        try:
            # Buscamos al usuario por email
            user = User.objects.get(email=correo)
        except User.DoesNotExist:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificamos que la cuenta esté activa
        if not user.is_active:
            return Response(
                {"error": "Cuenta inactiva, contacte al administrador"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verificamos la contraseña
        if user.check_password(password):
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": {
                    "id": user.id,
                    "correo": user.email,
                    "nombre": user.nombre,
                    "rol": user.rol,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    """
    Endpoint de Logout: requiere autenticación, y elimina el token asociado.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        # Borra el token del usuario actual
        request.user.auth_token.delete()
        return Response({"mensaje": "Sesión finalizada"}, status=status.HTTP_200_OK)