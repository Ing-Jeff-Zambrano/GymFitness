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
    peso = models.FloatField(blank=True, null=True)
    estatura = models.FloatField(blank=True, null=True)
    body_photos_data = models.TextField(blank=True, null=True,
                                        help_text="JSON array of base64 image data for body photos")

    def __str__(self):
        return f"Medición del {self.fecha_medicion.strftime('%Y-%m-%d')}"


# NUEVO MODELO: AnalisisPostura
class AnalisisPostura(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='analisis_posturas')
    ejercicio_nombre = models.CharField(max_length=100, help_text="Nombre del ejercicio analizado (ej. curl_biceps)")
    fecha_analisis = models.DateTimeField(auto_now_add=True)

    # Campo para el video original subido por el usuario
    # Considera usar FileField si el video va a ser grande, o TextField si vas a guardar base64 (no recomendado para videos grandes)
    video_original = models.FileField(upload_to='analisis_videos/originales/', blank=True, null=True,
                                      help_text="Archivo del video original subido por el usuario.")

    # Campo para el video procesado con anotaciones (ej. esqueleto detectado)
    # Puede ser nulo si el análisis no genera un video procesado
    video_procesado = models.FileField(upload_to='analisis_videos/procesados/', blank=True, null=True,
                                       help_text="Archivo del video con el análisis de postura (esqueleto, etc.).")

    feedback_texto = models.TextField(blank=True, null=True,
                                      help_text="Retroalimentación textual sobre la postura y técnica.")

    puntuacion_postura = models.FloatField(blank=True, null=True,
                                           help_text="Puntuación numérica de la postura (ej. 0.0 a 1.0, o 1 a 10).")

    # JSONField es ideal para guardar datos estructurados como ángulos o listas de errores.
    # Necesitarás importar `JSONField` si tu versión de Django es muy antigua, pero en las recientes ya viene.
    # Si JSONField da problemas, puedes usar TextField y guardar json.dumps(data) y json.loads(data)
    angulos_detectados = models.JSONField(blank=True, null=True,
                                          help_text="Ángulos y coordenadas clave detectadas en el video (formato JSON).")

    errores_detectados = models.JSONField(blank=True, null=True,
                                          help_text="Lista de errores de postura detectados (formato JSON).")

    def __str__(self):
        return f"Análisis de {self.ejercicio_nombre} por {self.usuario.username} ({self.fecha_analisis.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = "Análisis de Postura"
        verbose_name_plural = "Análisis de Posturas"
        ordering = ['-fecha_analisis']  # Ordenar por fecha de análisis descendente por defecto
