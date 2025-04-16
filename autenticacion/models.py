from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.db import models
import time

class CustomUser(AbstractUser):
    ROL_CHOICES = (
        ('Coordinador', 'Coordinador'),
        ('Vicerrector', 'Vicerrector'),
    )

    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Almacenaremos el hash de la contraseña
    rol = models.CharField(max_length=50, choices=ROL_CHOICES)
    programa = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def set_username(self):
        self.username = self.nombre.lower().replace(" ", "_")+str(time.time() * 1000)  # Cambia el username

    def set_email(self):
        self.email = self.correo  # Cambia el correo

    def __str__(self):
        return f"{self.nombre} ({self.rol})"
