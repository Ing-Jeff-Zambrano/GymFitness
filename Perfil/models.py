from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    fecha_nacimiento = models.DateField()
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
    github_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    google_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    tipo_cuerpo = models.CharField(max_length=50, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="gym_fitness_user_set",  # Añade un related_name único
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="gym_fitness_user_perm_set",  # Añade un related_name único
        related_query_name="user",
    )

    def __str__(self):
        return self.username