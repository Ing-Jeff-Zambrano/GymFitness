import os
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .analysis_logic import ANALYSIS_FUNCTIONS  # ¡Importa el diccionario de funciones de análisis!


@login_required
def analizar_video(request):
    """
    Vista para subir y analizar videos de ejercicios.
    Maneja la visualización del formulario (GET) y el análisis de videos (POST).
    Devuelve JSON con los resultados del análisis para solicitudes POST.
    """
    results = None
    video_url = None
    feedback_message = None
    error_message = None

    # Obtener las opciones de ejercicio para el menú desplegable (para GET y para el context)
    exercise_options = get_exercise_options()

    if request.method == 'POST':
        uploaded_file = request.FILES.get('video_file')
        exercise_id = request.POST.get('exercise_id')

        # Validaciones iniciales
        if not uploaded_file:
            error_message = "Error: No se seleccionó ningún archivo de video."
            return JsonResponse({"success": False, "error": error_message}, status=400)
        elif not exercise_id:
            error_message = "Error: No se seleccionó ningún ejercicio."
            return JsonResponse({"success": False, "error": error_message}, status=400)
        elif exercise_id not in ANALYSIS_FUNCTIONS:
            error_message = f"Error: Ejercicio no reconocido '{exercise_id}'. Por favor, selecciona un ejercicio válido."
            return JsonResponse({"success": False, "error": error_message}, status=400)

        # Configurar el almacenamiento de archivos (usando MEDIA_ROOT de settings.py)
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)

        # Construir la ruta segura para guardar el archivo temporalmente
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_videos')
        os.makedirs(temp_dir, exist_ok=True)  # Crea el directorio si no existe

        file_name = uploaded_file.name
        file_path = os.path.join(temp_dir, file_name)

        # Guardar el archivo subido
        try:
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # URL temporal para mostrar el video. Importante para el renderizado en el front.
            # Esta URL es relativa a MEDIA_URL
            video_url_for_frontend = settings.MEDIA_URL + 'temp_videos/' + file_name

            print(f"DEBUG: Video subido: {file_name}, PATH: {file_path}")

            # --- Lógica para llamar a la función de análisis ---
            analysis_function = ANALYSIS_FUNCTIONS[exercise_id]
            analysis_results = analysis_function(file_path)  # Ejecuta el análisis del video

            # Asegurarse de que el nombre del ejercicio en el resultado sea legible
            analysis_results['exercise'] = exercise_id.replace('_', ' ').title()

            # Añadir la URL del video a los resultados para que el frontend pueda mostrarlo
            analysis_results['video_url'] = video_url_for_frontend
            analysis_results['success'] = True  # Indicar que el análisis fue exitoso

            print(f"DEBUG: Análisis completado para {exercise_id}. Resultados: {analysis_results}")

            # Devolver los resultados del análisis como JSON
            return JsonResponse(analysis_results)

        except Exception as e:
            error_message = f"Error durante el análisis del video para {exercise_id}: {e}"
            print(f"ERROR: {error_message}")  # Imprime el error en la consola del servidor para depuración
            return JsonResponse({"success": False, "error": error_message}, status=500)
        finally:
            # ORIGINALMENTE AQUÍ SE ELIMINABA EL ARCHIVO.
            # LO COMENTAMOS TEMPORALMENTE PARA QUE EL FRONTEND PUEDA CARGAR EL VIDEO.
            # if os.path.exists(file_path):
            #     try:
            #         os.remove(file_path)
            #         print(f"DEBUG: Archivo temporal eliminado: {file_path}")
            #     except OSError as e:
            #         print(f"ERROR: No se pudo eliminar el archivo temporal {file_path}: {e}")
            pass  # Añadimos un 'pass' para que el bloque 'finally' no esté vacío

    # Si la solicitud es GET (carga inicial de la página), renderiza la plantilla HTML
    context = {
        'exercise_options': exercise_options,
        # Estas variables serán None para la carga inicial (GET)
        'results': results,
        'video_url': video_url,
        'feedback': feedback_message,
        'error_message': error_message,
    }
    return render(request, 'nutricion/index.html', context)


def get_exercise_options():
    """
    Función auxiliar para definir las opciones de ejercicio.
    Los 'id' deben coincidir con las claves que usarás en ANALYSIS_FUNCTIONS en analysis_logic.py.
    """
    return [
        {'id': 'curl_biceps', 'name': 'Curl de Bíceps'},
        {'id': 'extensiones_triceps', 'name': 'Extensiones de Tríceps'},
        {'id': 'press_hombros', 'name': 'Press de Hombros'},
        {'id': 'elevaciones_laterales', 'name': 'Elevaciones Laterales'},
        {'id': 'remo', 'name': 'Remo'},
        {'id': 'peso_muerto', 'name': 'Peso Muerto'},
        {'id': 'press_banca', 'name': 'Press de Banca'},
        {'id': 'apertura_mancuerna', 'name': 'Apertura con Mancuerna'},
    ]

