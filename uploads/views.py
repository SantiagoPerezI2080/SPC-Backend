import os
import pandas as pd
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from proyecciones.models import Curso


class UploadCSVView(APIView):
    """
    Recibe un CSV en formato multipart/form-data y lo guarda en MEDIA_ROOT/csvs/<file_type>.csv
    No valida columnas, acepta cualquier encabezado.
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

        # 2) Procesar solo si es el archivo "a"
        if file_type == 'a':
            try:
                # lee con separador punto y coma
                df = pd.read_csv(filepath, sep=';', engine='python')
            except Exception as e:
                return Response({'error': f'Error al leer CSV: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            # columnas esperadas en orden
            expected = ['Cod_Curso','Semestre','Nom_Curso','JORNADA','Grupo','Programa','Cupo_Max','No_Estud']
            missing = [c for c in expected if c not in df.columns]
            if missing:
                return Response({'error': f'Columnas faltantes: {missing}'}, status=status.HTTP_400_BAD_REQUEST)

            # Insertar un Curso por cada fila, sin eliminar duplicados
            created = 0
            errores = []
            for idx, row in df.iterrows():
                try:
                    Curso.objects.create(
                        cod_curso=int(row['Cod_Curso']),
                        semestre=str(row['Semestre']),
                        nom_curso=str(row['Nom_Curso']),
                        jornada=str(row['JORNADA']),
                        grupo=str(row['Grupo']),
                        programa=str(row['Programa']),
                        cupo_max=int(row['Cupo_Max']),
                        no_estudiantes=int(row['No_Estud']),
                    )
                    created += 1
                except Exception as e:
                    errores.append({'fila': idx, 'error': str(e)})

            return Response({
                'message': f'Archivo {file_type.upper()} cargado. '
                           f'{created} registros insertados.',
                'errores': errores
            }, status=status.HTTP_200_OK)

        return Response(
            {'message': f'Archivo {file_type.upper()} cargado correctamente y procesado'},
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