from django.shortcuts import render
from rest_framework import viewsets, permissions
from .serializers import *
from .models import *

class ProgramaViewSet(viewsets.ModelViewSet):
    queryset = Programa.objects.all()
    serializer_class = ProgramaSerializer
    permission_classes = [permissions.IsAuthenticated]

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated]

class ComportamientoCursoViewSet(viewsets.ModelViewSet):
    queryset = ComportamientoCurso.objects.all()
    serializer_class = ComportamientoCursoSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProyeccionViewSet(viewsets.ModelViewSet):
    queryset = Proyeccion.objects.all()
    serializer_class = ProyeccionSerializer
    permission_classes = [permissions.IsAuthenticated]
