from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    ROLES = [
        ('administrador', 'Administrador'),
        ('gerente', 'Gerente'),
        ('vendedor', 'Vendedor'),
        ('cocina', 'Cocina'),
    ]

    rol = models.CharField(max_length=20, choices=ROLES, default='vendedor')
    telefono = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

    @property
    def is_administrador(self):
        return self.rol == 'administrador'

    @property
    def is_gerente(self):
        return self.rol in ['administrador', 'gerente']

    @property
    def is_vendedor(self):
        return self.rol in ['administrador', 'gerente', 'vendedor']

    @property
    def is_cocina(self):
        return self.rol in ['administrador', 'gerente', 'cocina']
