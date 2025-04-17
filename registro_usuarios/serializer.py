from rest_framework import serializers
#from .models import RegistroU
from autenticacion.models import CustomUser

# Lista de programas permitidos para Coordinador
PROGRAMAS_PERMITIDOS = [
    "Coordinador Facultad Ciencias Sociales y Humanidades",
    "Coordinador Programa Licenciatura en Eduación Infantil",
    "Coordinador Facultad de Ciencias Administrativas Contables y Económicas",
    "Coordinador Programas Contaduría Pública",
    "Coordinador Finanzas y Negocios Internacionales",
    "Coordinador Facultad Ciencias Ambientales y Desarrollo Sostenible",
    "Coordinadora Programa Ingeniería Electrónica",
    "Coordinador Programa Ingeniería de Software y Computación",
    "Coordinación Entrenamiento Deportivo",
    "Coordinación Gobierno y Relaciones Internacionales",
    "Coordinador del programa de Ing. Ambiental y Saneamiento",
    "Coordinadora del programa de Ingeniería Civil",
]

class RegistroUSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'nombre', 'correo', 'password', 'rol', 'programa', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}  # No se debe exponer la contraseña
        }

    def validate(self, data):
        rol = data.get('rol')
        programa = data.get('programa')

        if rol == 'Coordinador':
            if not programa:
                raise serializers.ValidationError("El campo 'programa' es obligatorio para el rol Coordinador.")
            if programa not in PROGRAMAS_PERMITIDOS:
                raise serializers.ValidationError(
                    f"El programa '{programa}' no es válido. Debe ser uno de los siguientes: {', '.join(PROGRAMAS_PERMITIDOS)}"
                )
        elif rol == 'Vicerrector':
            if programa:
                raise serializers.ValidationError("No se debe seleccionar un programa para el rol Vicerrector.")
        elif rol == 'Administrador':
            if programa:
                raise serializers.ValidationError("No se debe seleccionar un programa para el rol Administrador.")
        else:
            raise serializers.ValidationError("El rol debe ser 'Administrador, ''Coordinador' o ' Vicerrector'.")
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = CustomUser(**validated_data)
        usuario.set_username()  # Cambia el username
        usuario.set_email()  # Cambia el username
        usuario.set_password(password)  # Encripta la contraseña
        usuario.save()
        # Aquí se puede implementar el envío de email de confirmación si se desea
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
