from django.db import models
from django.contrib.auth.hashers import make_password

class RegistroU(models.Model):
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

    def save(self, *args, **kwargs):
        # Si el objeto es nuevo y la contraseña no está hasheada, la encripta.
        if not self.pk:
            self.set_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.rol})"
