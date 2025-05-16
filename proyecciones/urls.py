from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'programas', ProgramaViewSet)
router.register(r'cursos', CursoViewSet)
router.register(r'comportamientos', ComportamientoCursoViewSet)
router.register(r'proyeccionesPreyFin', ProyeccionViewSet)

urlpatterns = [
    path('proyecciones/', include(router.urls)),
]
