from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Perfil(models.Model):
    TIPOS_USUARIO = [
        ('administrador', 'Administrador'),
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    tipo_usuario = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='cliente')
    foto_url = models.URLField(blank=True, verbose_name='Link da foto')

    def __str__(self):
        return f'Perfil de {self.usuario.username} - {self.tipo_usuario}'