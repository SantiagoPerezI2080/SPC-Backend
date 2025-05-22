from django.urls import path, include
from rest_framework import routers
from .views import *
from proyecciones import views
import urllib.parse

router = routers.DefaultRouter()
router.register(r'Proyeccion', views.ProyeccionView, 'Proyeccion')
router.register(r'comportamiento', views.VercomportamientoView, 'comportamiento')
router.register(r'cursos', views.VerCursosView, 'cursos')

router.register(r'programas', ProgramaViewSet)
router.register(r'cursos', CursoViewSet)
router.register(r'comportamientos', ComportamientoCursoViewSet)
router.register(r'proyeccionesPreyFin', ProyeccionViewSet)

urlpatterns = [
    path('proyecciones/', include(router.urls)),
    path('proyecciones/v1/',include(router.urls)),
    path('comportamiento/v1/',include(router.urls)),
    path('cursos/v1/',include(router.urls)),
    path('exportar-proyecciones/', views.exportar_proyecciones_csv, name='exportar_proyecciones'),
]
