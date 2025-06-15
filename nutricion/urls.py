from django.urls import path
from . import views

# Cambiamos el nombre de la aplicación para reflejar su nuevo propósito
app_name = 'analisis_postura'

urlpatterns = [
    # Ruta para la página de subida y análisis de video
    path('analizar-video/', views.analizar_video, name='analizar_video'),
    # Puedes añadir otras rutas aquí si las necesitas en el futuro
]