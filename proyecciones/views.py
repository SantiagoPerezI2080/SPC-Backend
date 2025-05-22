from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import *
from .models import *
from django.db.models import Sum
from django.shortcuts import render
from .models import Prerequisito, Curso, ComportamientoCurso, Proyeccion

from django.http import HttpResponse
import csv
from django.http import HttpResponse
from django.db.models import Q

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

    # Genera la proyección final
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
                    # Se hace la operación para calcular el número de estudiantes
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

# Genera la proyeción preliminar
    @action(detail=False, methods=['post'], url_path='generate_preliminar')
    def generate_preliminar(self, request):
        """
        Genera proyecciones preliminares usando la tabla Prerequisito + Curso.
        Payload esperado: { anio, periodo, version }  (version = 'Preliminar')
        """
        anio     = request.data.get('anio')
        periodo  = request.data.get('periodo')
        version  = request.data.get('version')

        if not all([anio, periodo, version]):
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

        # Eliminamos previas de esta combo
        Proyeccion.objects.filter(anio=anio, periodo=periodo, version=version).delete()

        created = 0
        prereqs = Prerequisito.objects.all()
        for pr in prereqs:
            # <-- CAMBIO: use filter() en lugar de get() para múltiples grupos
            matching_courses = Curso.objects.filter(
                cod_curso=pr.cod_curso,
                semestre=pr.semestre,
                nom_curso=pr.nom_curso
            )
            for curso in matching_courses:
                # Aquí tu lógica de preliminar (placeholder)
                no_est = curso.no_estudiantes

                Proyeccion.objects.create(
                    anio=anio,
                    periodo=periodo,
                    version=version,
                    programa=curso.programa,
                    semestre=curso.semestre,
                    curso=curso.nom_curso,
                    grupo=curso.grupo,            # ahora itera por cada grupo
                    cupo_max=curso.cupo_max,
                    no_estud_final=no_est
                )
                created += 1

        return Response(
            {'message': f'Se generaron {created} proyecciones preliminares.'},
            status=status.HTTP_200_OK
        )

class ProyeccionView (viewsets.ModelViewSet):
    serializer_class = ProyeccionSerializer
    queryset = Proyeccion.objects.all()

class VercomportamientoView (viewsets.ModelViewSet):
    serializer_class = ComportamientoCursoSerializer
    queryset = ComportamientoCurso.objects.all()

class VerCursosView (viewsets.ModelViewSet):
    serializer_class = CursoSerializer
    queryset = Curso.objects.all()

#endpoint de descarga csv (http://localhost:8000/proyeccion/exportar-proyecciones)
def exportar_proyecciones_csv(request):
    # Lista de programas permitidos
    programas_permitidos = [
        "EDUCACION INFANTIL",
        "CONTADURIA PUBLICA",
        "FINANZAS Y NEGOCIOS INTERNACIONALES",
        "INGENIERIA ELECTRONICA",
        "INGENIERIA DE SOFTWARE Y COMPUTACION",
        "ENTRENAMIENTO DEPORTIVO",
        "GOBIERNO Y RELACIONES INTERNACIONALES",
        "INGENIERIA AMBIENTAL Y SANEAMIENTO",
        "INGENIERIA CIVIL",
    ]

    # Obtener filtros de la solicitud GET
    programa = request.GET.get('programa', None)
    anio = request.GET.get('anio', None)
    periodo = request.GET.get('periodo', None)
    version = request.GET.get('version', None)

    # Normalizar el programa
    if programa:
        programa = programa.replace('%20', ' ').strip().upper()  # Manejar '%20' y estandarizar a mayúsculas
        if programa not in programas_permitidos:
            return HttpResponse(
                f"El programa '{programa}' proporcionado no es válido.",
                content_type="text/plain",
                status=400
            )

    # Depurar: Imprimir valores únicos del campo programa en la base de datos
    print("Programas únicos disponibles en la base de datos:")
    print(list(Proyeccion.objects.values_list('programa', flat=True)))

    # Aplicar filtros al queryset
    queryset = Proyeccion.objects.all()

    # Filtrar por programa
    if programa:
        queryset = queryset.filter(Q(programa__iexact=programa) | Q(programa__icontains=programa))

    # Filtrar por otros criterios
    if anio:
        queryset = queryset.filter(anio=anio)
    if periodo:
        queryset = queryset.filter(periodo=periodo)
    if version:
        queryset = queryset.filter(version=version)

    # Depurar: Registrar la consulta SQL generada
    print(f"Consulta SQL generada: {str(queryset.query)}")

    # Verificar si hay datos
    if not queryset.exists():
        return HttpResponse(
            f"No se encontraron datos para el filtro aplicado: Programa={programa}, Año={anio}, Periodo={periodo}, Versión={version}.",
            content_type="text/plain",
            status=404
        )

    # Depurar: Imprimir los datos encontrados después del filtro
    print("Datos encontrados después del filtro:")
    print(list(queryset.values()))

    # Serializar los datos
    serializer = ProyeccionSerializer(queryset, many=True)

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="proyecciones.csv"'

    # Especificar el delimitador como punto y coma
    writer = csv.writer(response, delimiter=';')

    # Obtener encabezados desde las claves del serializer
    if serializer.data:
        writer.writerow(serializer.data[0].keys())  # Escribir encabezados

        for item in serializer.data:
            writer.writerow(item.values())  # Escribir cada fila

    return response