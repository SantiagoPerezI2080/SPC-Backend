from django.db import models

class Programa(models.Model):
    id_programa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    codigo_snies = models.IntegerField()
    registro_calificado = models.CharField(max_length=300)
    creditos = models.IntegerField()
    titulo = models.CharField(max_length=100)
    metodologia = models.CharField(max_length=100)
    duracion = models.CharField(max_length=100)

class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True)
    cod_curso = models.IntegerField()
    semestre = models.CharField(max_length=100)
    nom_curso = models.CharField(max_length=100)
    jornada = models.CharField(max_length=50)
    grupo = models.CharField(max_length=50)
    programa = models.CharField(max_length=100)
    cupo_max = models.IntegerField()
    no_estudiantes = models.IntegerField()

    def __str__(self):
        return f"{self.cod_curso} – {self.nom_curso}"

class ComportamientoCurso(models.Model):
    id_comportamiento = models.AutoField(primary_key=True)
    programa = models.CharField(max_length=100)
    cod_curso = models.IntegerField()
    cod_semestre = models.CharField(max_length=50)
    semestre = models.CharField(max_length=50)
    nom_curso = models.CharField(max_length=100)
    cod_jornada = models.CharField(max_length=50)
    jornada = models.CharField(max_length=50)
    grupo = models.CharField(max_length=50)
    no_estudiantes = models.IntegerField()
    prom_nota = models.FloatField()
    habilitan = models.IntegerField()
    pierdenh = models.IntegerField()
    pierden_total = models.IntegerField()

    def __str__(self):
        return super().__str__()

class Proyeccion(models.Model):
    id_proyeccion = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    periodo = models.IntegerField()
    version = models.CharField(max_length=50)
    programa = models.CharField(max_length=100)
    semestre = models.CharField(max_length=50)
    curso = models.CharField(max_length=100)
    grupo = models.CharField(max_length=50)
    cupo_max = models.IntegerField()
    no_estud_final = models.IntegerField(default=0)
    

    def __str__(self):
        return super().__str__()
    
class Prerequisito(models.Model):
    cod_curso = models.IntegerField()
    semestre = models.CharField(max_length=50)
    cod_semestre = models.IntegerField()
    nom_curso = models.CharField(max_length=90)
    prerrequisito = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.cod_semestre} - {self.nom_curso}: {self.prerrequisito}"