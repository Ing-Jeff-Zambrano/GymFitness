from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

# Importaciones para OpenCV y MediaPipe (aunque la lógica de análisis se añadirá después)
import cv2
import mediapipe as mp

# Inicialización de MediaPipe (se usará en futuras fases)
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils


@login_required
def analizar_video(request):
    """
    Vista para subir y analizar videos de ejercicios.
    Maneja la visualización de la página y la subida de archivos.
    """
    if request.method == 'POST' and request.FILES.get('video_ejercicio'):
        # Obtener el archivo de video subido
        video_file = request.FILES['video_ejercicio']

        # Configurar el almacenamiento de archivos (usando MEDIA_ROOT de settings.py)
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)

        # Guardar el archivo de video en el directorio MEDIA_ROOT
        # Generamos un nombre de archivo único para evitar colisiones
        filename = fs.save(video_file.name, video_file)
        uploaded_file_url = fs.url(filename)

        print(f"DEBUG: Video subido: {filename}, URL: {uploaded_file_url}")

        # --- Aquí iría la lógica inicial para procesar el video ---
        # Por ahora, solo confirmamos la subida y pasamos la URL al template
        # La lógica de análisis de postura con OpenCV/MediaPipe se añadirá aquí en la siguiente fase.

        # Ejemplo de cómo podrías empezar a usar OpenCV (solo un placeholder)
        # video_path = os.path.join(settings.MEDIA_ROOT, filename)
        # cap = cv2.VideoCapture(video_path)
        # if cap.isOpened():
        #     print(f"DEBUG: Video {filename} abierto con éxito para análisis.")
        #     cap.release()
        # else:
        #     print(f"ERROR: No se pudo abrir el video {filename} con OpenCV.")

        context = {
            'uploaded_file_url': uploaded_file_url,
            'message': 'Video subido exitosamente. ¡Listo para el análisis de postura!',
            'success': True
        }
        return render(request, 'nutricion/index.html', context)

    # Si es una petición GET, simplemente renderizamos la página vacía
    return render(request, 'nutricion/index.html', {})
