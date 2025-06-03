from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(
        max_length=1,
        choices=(
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('O', 'Otro'),
        )
    )
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfil_pics/', blank=True, null=True)
    peso = models.FloatField(blank=True, null=True)  # Nuevo campo para el peso
    estatura = models.FloatField(blank=True, null=True)
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="gym_fitness_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="gym_fitness_user_perm_set",
        related_query_name="user",
    )

    def __str__(self):
        return self.username

class MedicionCuerpo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mediciones_cuerpo')
    fecha_medicion = models.DateTimeField(auto_now_add=True)
    ancho_hombros = models.FloatField(blank=True, null=True)
    ancho_caderas = models.FloatField(blank=True, null=True)
    icc_estimado = models.FloatField(blank=True, null=True)
    relacion_hombro_cintura = models.FloatField(blank=True, null=True)
    tipo_cuerpo = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Medición de {self.usuario.username} el {self.fecha_medicion.strftime('%Y-%m-%d %H:%M:%S')}"