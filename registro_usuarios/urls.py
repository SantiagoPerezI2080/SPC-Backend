from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from registro_usuarios import views

router = routers.DefaultRouter()
router.register(r'registro', views.RegistroUViewSet, 'registro_usuarios')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path("docs/", include_docs_urls(title="Registro usuarios API")),
]