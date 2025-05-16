from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import *
from .models import *
from django.db.models import Sum
from django.shortcuts import render
from .models import Curso, ComportamientoCurso, Proyeccion

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

    @action(detail=False, methods=['post'], url_path='generate')  # MODIFICADO: ya no pide programa
    def generate(self, request):
        """
        Genera las proyecciones finales sin solicitar programa.
        Payload esperado: { anio, periodo, version }
        Los programas se obtienen de los registros en ComportamientoCurso.
        """
        anio    = request.data.get('anio')
        periodo = request.data.get('periodo')
        version = request.data.get('version')

        # Validaciones básicas
        if not all([anio, periodo, version]):
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

        # Limpiar proyecciones previas para esta versión
        Proyeccion.objects.filter(anio=anio, periodo=periodo, version=version).delete()

        created = 0
        # Obtiene los programas de los comportamientos
        programas = ComportamientoCurso.objects.values_list('programa', flat=True).distinct()
        for prog in programas:
            cursos = Curso.objects.filter(programa=prog)
            for curso in cursos:
                comps = ComportamientoCurso.objects.filter(
                    programa=prog,
                    cod_curso=curso.cod_curso,
                    semestre=curso.semestre,
                    nom_curso=curso.nom_curso,
                    grupo=curso.grupo
                )
                for comp in comps:
                    no_est = curso.no_estudiantes - comp.pierden_total
                    Proyeccion.objects.create(
                        anio=anio,
                        periodo=periodo,
                        version=version,
                        programa=prog,
                        semestre=curso.semestre,
                        curso=curso.nom_curso,
                        grupo=curso.grupo,
                        cupo_max=curso.cupo_max,
                        no_estud_final=no_est
                    )
                    created += 1
        return Response({'message': f'Se generaron {created} proyecciones.'}, status=status.HTTP_200_OK)
