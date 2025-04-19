from rest_framework import serializers
from .models import *

class ProgramaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Programa
        fields = '__all__'

class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = '__all__'

class ComportamientoCursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComportamientoCurso
        fields = '__all__'

class ProyeccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proyeccion
        fields = '__all__'