import os
import pandas as pd
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from proyecciones.models import Curso, ComportamientoCurso


class UploadCSVView(APIView):
    """
    Recibe un CSV en multipart/form-data, lo guarda en MEDIA_ROOT/csvs/<file_type>.csv
    y si file_type == 'a' lo procesa hacia Curso,
    si file_type == 'b' lo procesa hacia ComportamientoCurso (limpiando antes la tabla).
    """
    parser_classes = [MultiPartParser]

    def post(self, request, file_type, format=None):
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({'error': 'No se ha enviado ningún archivo'}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Guardar en disco
        target_dir = os.path.join(settings.MEDIA_ROOT, 'csvs')
        os.makedirs(target_dir, exist_ok=True)
        filename = f"{file_type}.csv"
        filepath = os.path.join(target_dir, filename)
        with open(filepath, 'wb+') as f:
            for chunk in csv_file.chunks():
                f.write(chunk)

        # 2) Procesar según tipo
        if file_type == 'a':
            # <-- LIMPIAR LA TABLA Curso antes de cargar
            Curso.objects.all().delete()
            # === tu lógica actual para a tabla Curso ===
            try:
                df = pd.read_csv(filepath, sep=';', engine='python')
            except Exception as e:
                return Response({'error': f'Error al leer CSV A: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            expected = ['Cod_Curso','Semestre','Nom_Curso','JORNADA','Grupo','Programa','Cupo_Max','No_Estud']
            missing = [c for c in expected if c not in df.columns]
            if missing:
                return Response({'error': f'Columnas faltantes en A: {missing}'}, status=status.HTTP_400_BAD_REQUEST)

            for _, row in df.iterrows():
                Curso.objects.create(
                    cod_curso=int(row['Cod_Curso']),
                    semestre=row['Semestre'],
                    nom_curso=row['Nom_Curso'],
                    jornada=row['JORNADA'],
                    grupo=row['Grupo'],
                    programa=row['Programa'],
                    cupo_max=int(row['Cupo_Max']),
                    no_estudiantes=int(row['No_Estud']),
                )

        elif file_type == 'b':
            # === nueva lógica para B tabla ComportamientoCurso ===
            try:
                df = pd.read_csv(filepath, sep=';', engine='python')
            except Exception as e:
                return Response({'error': f'Error al leer CSV B: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            expected_b = [
                'Programa','Cod_Curso','Cod_semestre','Semestre','Nom_Curso',
                'Cod_Jornada','JORNADA','Grupo','No_Estud',
                'Prom_Nota','Habilitan','PierdenH','Pierden_Total'
            ]
            missing_b = [c for c in expected_b if c not in df.columns]
            if missing_b:
                return Response({'error': f'Columnas faltantes en B: {missing_b}'}, status=status.HTTP_400_BAD_REQUEST)

            # Limpia tabla ComportamientoCurso
            ComportamientoCurso.objects.all().delete()

            # Inserta siempre un nuevo registro por fila
            for _, row in df.iterrows():
                # Extraemos el valor original como string y sustituimos "," por "."
                raw_prom = str(row['Prom_Nota']).strip()
                prom = 0.0
                if raw_prom and raw_prom.lower() not in {'nan', 'none'}:
                    prom = float(raw_prom.replace(',', '.'))

                ComportamientoCurso.objects.create(
                    programa=row['Programa'],
                    cod_curso=int(row['Cod_Curso']),
                    cod_semestre=str(row['Cod_semestre']),
                    semestre=row['Semestre'],
                    nom_curso=row['Nom_Curso'],
                    cod_jornada=str(row['Cod_Jornada']),
                    jornada=row['JORNADA'],
                    grupo=row['Grupo'],
                    no_estudiantes=int(row['No_Estud']),
                    prom_nota=prom,
                    habilitan=int(row['Habilitan']),
                    pierdenh=int(row['PierdenH']),
                    pierden_total=int(row['Pierden_Total']),
                )

        elif file_type == 'prerrequisitos':
            from proyecciones.models import Prerequisito
            # guardar y luego limpiar
            Prerequisito.objects.all().delete()
            try:
                df = pd.read_csv(filepath, sep=';', engine='python')
            except Exception as e:
                return Response({'error': f'Error al leer CSV prerrequisitos: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
            expected_pr = ['Cod_Curso','Semestre','Cod_Semestre','Nom_Curso','Prerrequisito']
            missing_pr = [c for c in expected_pr if c not in df.columns]
            if missing_pr:
                return Response({'error': f'Columnas faltantes en prerrequisitos: {missing_pr}'}, status=status.HTTP_400_BAD_REQUEST)
            for _, row in df.iterrows():
                Prerequisito.objects.create(
                    cod_curso=int(row['Cod_Curso']),
                    semestre=row['Semestre'],
                    cod_semestre=int(row['Cod_Semestre']),
                    nom_curso=row['Nom_Curso'],
                    prerrequisito=row['Prerrequisito'],
                )

        else:
            # tipo no soportado
            return Response({'error': f'Tipo de archivo "{file_type}" no soportado'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'message': f'Archivo {file_type.upper()} cargado y procesado correctamente'},
            status=status.HTTP_200_OK
        )

class ListUploadedCSVs(APIView):
    """
    Devuelve la lista de CSVs cargados (basado en archivos en MEDIA_ROOT/csvs).
    """
    def get(self, request):
        folder = os.path.join(settings.MEDIA_ROOT, 'csvs')
        if not os.path.isdir(folder):
            return Response([], status=status.HTTP_200_OK)
        files = [f for f in os.listdir(folder) if f.lower().endswith('.csv')]
        # Devolver sin extensión
        types = [os.path.splitext(f)[0] for f in files]
        return Response({'types': types}, status=status.HTTP_200_OK)

# uploads/views.py

class PreviewCSV(APIView):
    """
    Lee un CSV cargado y devuelve las primeras filas (hasta 20).
    Intenta autodetectar delimitador y encoding.
    URL: /api/uploaded/<file_type>/preview/
    """
    def get(self, request, file_type):
        path = os.path.join(settings.MEDIA_ROOT, 'csvs', f"{file_type}.csv")
        if not os.path.isfile(path):
            return Response({'error': 'Archivo no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Tratamos de leer con autodetección de delimitador y fallback de encoding
        try:
            # engine python + sep=None hará sniff del delimitador
            df = pd.read_csv(path, sep=None, engine='python')
        except Exception:
            try:
                # si falla, probamos con encoding latin-1 (a veces necesario en Windows)
                df = pd.read_csv(path, sep=None, engine='python', encoding='latin-1')
            except Exception as e:
                return Response(
                    {'error': f'No se pudo leer CSV: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        data = df.head(20).to_dict(orient='records')
        columns = list(df.columns)
        return Response({'columns': columns, 'rows': data}, status=status.HTTP_200_OK)