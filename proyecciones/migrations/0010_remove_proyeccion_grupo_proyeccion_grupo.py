# Generated by Django 5.1.7 on 2025-05-16 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyecciones', '0009_rename_no_estudiantes_proyeccion_no_estud_final'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proyeccion',
            name='Grupo',
        ),
        migrations.AddField(
            model_name='proyeccion',
            name='grupo',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
    ]
