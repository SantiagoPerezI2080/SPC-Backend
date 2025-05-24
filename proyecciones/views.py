from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import *
from .models import *
from django.db.models import Sum
from django.shortcuts import render
from math import ceil
import math

from .models import Prerequisito, Curso, ComportamientoCurso, Proyeccion
from django.http import HttpResponse
import csv
from django.http import HttpResponse
from django.db.models import Q


SEMESTRE_MAP = {
    1: 'PRIMER SEMESTRE',
    2: 'SEGUNDO SEMESTRE',
    3: 'TERCER SEMESTRE',
    4: 'CUARTO SEMESTRE',
    5: 'QUINTO SEMESTRE',
    6: 'SEXTO SEMESTRE',
    7: 'SEPTIMO SEMESTRE',
    8: 'OCTAVO SEMESTRE',
    9: 'NOVENO SEMESTRE',
}

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
    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        """
        Genera las proyecciones finales sin selector de programa.
        Lógica:
        1. Para cada programa distinto en ComportamientoCurso...
        2. Para cada curso (cod_curso, semestre, nom_curso) de ese programa:
           a) Sumar (no_estudiantes - pierden_total) de todos los grupos -> total_final
           b) Calcular cupo_medio_dest = ceil(promedio de cupo_max en Curso destino)
           c) n_grupos = ceil(total_final / cupo_medio_dest)
           d) size_grupo = ceil(total_final / n_grupos)
           e) Crear n_grupos filas A, B, C… con cupo_max = cupo_medio_dest y no_estud_final = size_grupo
        """
        anio    = request.data.get('anio')
        periodo = request.data.get('periodo')
        version = request.data.get('version')
        if not all([anio, periodo, version]):
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

        # 0) limpieza
        Proyeccion.objects.filter(anio=anio, periodo=periodo, version=version).delete()

        created = 0
        programas = ComportamientoCurso.objects.values_list('programa', flat=True).distinct()

        for prog in programas:
            # cursos únicos en comportamiento para este programa
            cursos_keys = ComportamientoCurso.objects.filter(programa=prog) \
                .values('cod_curso','semestre','nom_curso') \
                .distinct()

            for key in cursos_keys:
                cod = key['cod_curso']
                sem = key['semestre']
                nombre = key['nom_curso']

                # a) total_final
                comps = ComportamientoCurso.objects.filter(
                    programa=prog,
                    cod_curso=cod,
                    semestre=sem,
                    nom_curso=nombre
                )
                total_final = sum(c.no_estudiantes - c.pierden_total for c in comps)

                # b) cupo medio en Curso destino
                cursos_dest = Curso.objects.filter(cod_curso=cod, semestre=sem, nom_curso=nombre)
                cupos = [c.cupo_max for c in cursos_dest]
                if not cupos:
                    continue  # no hay datos de cupo, saltar
                cupo_medio = ceil(sum(cupos) / len(cupos))

                # c) número de grupos nuevos
                n_grupos = ceil(total_final / cupo_medio) if cupo_medio > 0 else 1

                # d) tamaño de cada grupo
                size_grupo = ceil(total_final / n_grupos) if n_grupos > 0 else 0

                # e) crear filas A, B, C…
                for i in range(n_grupos):
                    grupo = chr(ord('A') + i)
                    Proyeccion.objects.create(
                        anio=anio,
                        periodo=periodo,
                        version=version,
                        programa=prog,
                        semestre=sem,
                        curso=nombre,
                        grupo=grupo,
                        cupo_max=cupo_medio,
                        no_estud_final=size_grupo
                    )
                    created += 1

        return Response(
            {'message': f'Se generaron {created} proyecciones finales.'},
            status=status.HTTP_200_OK
        )

# Genera la proyeción preliminar
    @action(detail=False, methods=['post'], url_path='generate_preliminar')
    def generate_preliminar(self, request):
        anio     = request.data.get('anio')
        periodo  = request.data.get('periodo')
        version  = request.data.get('version')
        if not all([anio, periodo, version]):
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

        # Borro las preliminares previas
        Proyeccion.objects.filter(anio=anio, periodo=periodo, version=version).delete()

        created = 0

        for pr in Prerequisito.objects.all().order_by('cod_semestre'):
            prev_code = pr.cod_semestre - 1
            prev_sem  = SEMESTRE_MAP.get(prev_code)

            # 1) Calcular no_est_final
            if pr.prerrequisito.upper() == 'PROM':
                # TODOS los cursos del semestre anterior
                prev_cursos = Curso.objects.filter(semestre=prev_sem) if prev_sem else Curso.objects.none()

                # promedio por curso
                avg_por_curso = []
                for nombre in prev_cursos.values_list('nom_curso', flat=True).distinct():
                    group = prev_cursos.filter(nom_curso=nombre)
                    total = sum(c.no_estudiantes for c in group)
                    avg_por_curso.append(total / group.count())

                no_est_final = math.ceil(sum(avg_por_curso) / len(avg_por_curso)) if avg_por_curso else 0

                # heredo grupos y cupos de TODO prev_cursos
                grupos = sorted({c.grupo for c in prev_cursos})
                cupos = [c.cupo_max for c in prev_cursos]
                cupo_final = math.ceil(sum(cupos) / len(cupos)) if cupos else 0

            else:
                # solo aquellos cursos cuyo nom_curso es el prerrequisito
                mismos = Curso.objects.filter(
                    nom_curso=pr.prerrequisito,
                    semestre=prev_sem
                ) if prev_sem else Curso.objects.none()

                total = sum(c.no_estudiantes for c in mismos)
                no_est_final = math.ceil(total / mismos.count()) if mismos.exists() else 0

                grupos = sorted({c.grupo for c in mismos})
                cupos = [c.cupo_max for c in mismos]
                cupo_final = math.ceil(sum(cupos) / len(cupos)) if cupos else 0

            # 2) Inserto una Proyección por cada grupo calculado
            programa = prev_cursos.first().programa if pr.prerrequisito.upper()=='PROM' and prev_cursos.exists() \
                       else (mismos.first().programa if mismos.exists() else '')
            for g in grupos:
                Proyeccion.objects.create(
                    anio=anio,
                    periodo=periodo,
                    version=version,
                    programa=programa,
                    semestre=pr.semestre,
                    curso=pr.nom_curso,
                    grupo=g,
                    cupo_max=cupo_final,
                    no_estud_final=no_est_final
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
