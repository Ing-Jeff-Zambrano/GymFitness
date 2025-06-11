import base64
import numpy as np
import cv2
import mediapipe as mp
import json
import io
from PIL import Image

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.files.base import ContentFile
from django.views.decorators.cache import never_cache
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import SignUpForm, LoginForm, UserProfileForm
from .models import Usuario, MedicionCuerpo

from datetime import datetime, date

User = get_user_model()

# Inicialización global de MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils


def procesar_imagen_tipo_cuerpo(image_data_url):
    """
    Procesa una imagen base64 para detectar puntos de pose con MediaPipe.
    Retorna los landmarks, ancho y alto de la imagen si se detectan poses,
    de lo contrario, retorna None, ancho, alto.
    """
    try:
        image_str = image_data_url.split(',')[1]
        image_bytes = base64.b64decode(image_str)

        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_array = np.array(image)

        img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        alto, ancho, _ = img_cv2.shape

        resultados = pose.process(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))

        if resultados.pose_landmarks:
            print(f"DEBUG: Pose detectada en la imagen. Ancho: {ancho}, Alto: {alto}")
            return resultados.pose_landmarks.landmark, ancho, alto
        else:
            print("DEBUG: No se detectaron puntos de pose en la imagen.")
            return None, ancho, alto
    except Exception as e:
        print(f"ERROR: Fallo al procesar la imagen en procesar_imagen_tipo_cuerpo: {e}")
        return None, None, None


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Nombre de usuario o contraseña inválidos.')
                return render(request, 'perfil/login.html', {'form': form})
        else:
            messages.error(request, 'Formulario inválido. Por favor, revisa tus datos.')
            return render(request, 'perfil/login.html', {'form': form})
    else:
        form = AuthenticationForm()
    return render(request, 'perfil/login.html', {'form': form})


def register(request):
    msg = None
    success = False
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.fecha_nacimiento = date.today()
            user.save()
            msg = 'Usuario creado - por favor, <a href="/">inicia sesión</a>.'
            success = True
        else:
            msg = 'El formulario no es válido'
            print("Errores en el formulario de registro:", form.errors)
    else:
        form = SignUpForm()
    return render(request, 'perfil/register.html', {"form": form, "msg": msg, "success": success})


@never_cache
@login_required
def dashboard(request):
    # Obtener la última medición del cuerpo para el usuario actual
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    # Obtener el tipo de cuerpo de la última medición
    tipo_cuerpo = "No determinado"
    if ultima_medicion and ultima_medicion.tipo_cuerpo:
        tipo_cuerpo = ultima_medicion.tipo_cuerpo

    # --- LÓGICA PARA LA TABLA DE MEDICIONES RECIENTES EN EL DASHBOARD ---
    mediciones_recientes = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion')[:5]

    # Calcular IMC para cada medición en la lista (para la tabla)
    for medicion in mediciones_recientes:
        imc_calculado_para_medicion = None
        if medicion.peso is not None and medicion.estatura is not None and medicion.estatura > 0:
            estatura_m = float(medicion.estatura) / 100.0
            if estatura_m > 0:
                imc_calculado_para_medicion = round(float(medicion.peso) / (estatura_m ** 2), 2)
        medicion.imc_valor = imc_calculado_para_medicion

    # --- NUEVA LÓGICA: Preparar datos para el gráfico de peso D3.js en el dashboard ---
    mediciones_para_d3_dashboard = MedicionCuerpo.objects.filter(usuario=request.user).order_by('fecha_medicion')
    data_peso_dashboard = []
    for med in mediciones_para_d3_dashboard:
        if med.peso is not None and med.fecha_medicion is not None:
            data_peso_dashboard.append({
                'fecha': med.fecha_medicion.strftime('%Y-%m-%d'),
                'peso': float(med.peso)
            })
    fechas_pesos_json_dashboard = json.dumps(data_peso_dashboard, default=str)

    context = {
        'tipo_cuerpo': tipo_cuerpo,
        'ultima_medicion': ultima_medicion,
        'mediciones_recientes': mediciones_recientes,
        'fechas_pesos_json_dashboard': fechas_pesos_json_dashboard,
        # 'is_authenticated_user': request.user.is_authenticated, # Ya no es necesario con el nuevo JS
    }
    return render(request, 'perfil/dashboard.html', context)


@never_cache
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


@login_required
def perfil(request):
    # Obtener la última medición al inicio
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    form = UserProfileForm(instance=request.user)  # Inicializar el formulario de perfil

    if request.method == 'POST':
        files_data = request.FILES.copy()

        # --- MODIFICADO: Procesamiento de Foto de Perfil (si aplica) ---
        camera_photo_data = request.POST.get('camera_photo_data')
        if camera_photo_data:
            try:
                format, imgstr = camera_photo_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'{request.user.username}_perfil.{ext}')
                files_data['foto_perfil'] = data
                messages.success(request, "Foto de perfil capturada y lista para guardar.")
            except Exception as e:
                messages.error(request, f"Hubo un error al procesar la foto de la cámara: {e}")

        form = UserProfileForm(request.POST, files_data, instance=request.user)

        # --- MODIFICADO: Extracción y validación de peso y estatura ---
        peso_kg = None
        estatura_cm = None

        peso_input_str = request.POST.get('peso')
        estatura_input_str = request.POST.get('estatura')

        if peso_input_str and peso_input_str.strip() != '':
            try:
                peso_kg = float(peso_input_str)
            except ValueError:
                messages.error(request, "El peso ingresado no es un número válido.")
                peso_kg = None  # Asegurar que sea None si es inválido

        if estatura_input_str and estatura_input_str.strip() != '':
            try:
                estatura_cm = float(estatura_input_str)
            except ValueError:
                messages.error(request, "La estatura ingresada no es un número válido.")
                estatura_cm = None  # Asegurar que sea None si es inválido

        # --- NUEVO: Cálculo del IMC (obligatorio para clasificación) ---
        imc_valor = None
        if peso_kg is not None and estatura_cm is not None and estatura_cm > 0:
            estatura_m = float(estatura_cm) / 100.0
            if estatura_m > 0:
                imc_valor = round(peso_kg / (estatura_m ** 2), 2)

        # --- MODIFICADO: Procesamiento de Fotos de Medición (para detección de cuerpo) ---
        body_photos_data = []  # Lista para almacenar las fotos procesadas en base64
        promedio_ancho_hombros = None
        promedio_ancho_caderas = None
        has_valid_photo_landmarks = False  # Flag para indicar si se obtuvieron landmarks válidos de las fotos

        measurement_photo_data_json = request.POST.get('measurement_photo_data')

        if measurement_photo_data_json and json.loads(measurement_photo_data_json):
            try:
                body_photos_data = json.loads(measurement_photo_data_json)
            except json.JSONDecodeError:
                messages.error(request, "Error al procesar los datos de las fotos de medición.")
                body_photos_data = []

            if body_photos_data:
                hombros_anchos_temp = []
                caderas_anchas_temp = []

                for i, image_data_url in enumerate(body_photos_data):
                    landmarks, ancho, alto = procesar_imagen_tipo_cuerpo(image_data_url)

                    min_conf_deteccion = 0.7  # Umbral de confianza para landmarks
                    if landmarks and \
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].visibility > min_conf_deteccion and \
                            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].visibility > min_conf_deteccion and \
                            landmarks[mp_pose.PoseLandmark.LEFT_HIP].visibility > min_conf_deteccion and \
                            landmarks[mp_pose.PoseLandmark.RIGHT_HIP].visibility > min_conf_deteccion:

                        hombro_izquierdo_px = int(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x * ancho)
                        hombro_derecho_px = int(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * ancho)
                        ancho_hombros_px = abs(hombro_derecho_px - hombro_izquierdo_px)
                        hombros_anchos_temp.append(ancho_hombros_px)

                        cadera_izquierda_px = int(landmarks[mp_pose.PoseLandmark.LEFT_HIP].x * ancho)
                        cadera_derecha_px = int(landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x * ancho)
                        ancho_caderas_px = abs(cadera_derecha_px - cadera_izquierda_px)
                        caderas_anchas_temp.append(ancho_caderas_px)
                    else:
                        print(
                            f"DEBUG: Foto {i + 1} - No se detectaron landmarks o visibilidad baja. Saltando foto para cálculo de medidas.")

                if hombros_anchos_temp and caderas_anchas_temp and len(hombros_anchos_temp) > 0 and len(
                        caderas_anchas_temp) > 0:
                    promedio_ancho_hombros = sum(hombros_anchos_temp) / len(hombros_anchos_temp)
                    promedio_ancho_caderas = sum(caderas_anchas_temp) / len(caderas_anchas_temp)
                    has_valid_photo_landmarks = True
                else:
                    print("DEBUG: No se obtuvieron promedios válidos de hombros/caderas de las fotos.")
            else:
                messages.warning(request, "Se intentó la detección de cuerpo, pero no se recibieron fotos.")
                print("DEBUG: No se recibieron fotos de medición para procesar.")

        # --- NUEVO: Lógica de Clasificación del Tipo de Cuerpo (IMC y FOTOS OBLIGATORIOS) ---
        determined_body_type = "No se pudo establecer el tipo de cuerpo, datos insuficientes o en posición INCORRECTA"
        relacion_hombro_cadera_simple = None

        # Validar si ambos tipos de datos (fotos y IMC) son válidos y están presentes
        is_photo_data_available_and_valid = (
                    has_valid_photo_landmarks and promedio_ancho_caderas is not None and promedio_ancho_caderas > 0)
        is_imc_data_available_and_valid = (imc_valor is not None)

        if is_photo_data_available_and_valid and is_imc_data_available_and_valid:
            relacion_hombro_cadera_simple = promedio_ancho_hombros / promedio_ancho_caderas

            # Lógica de clasificación combinada
            if imc_valor < 18.5:
                determined_body_type = "Ectomorfo"
            elif imc_valor >= 25.0:
                determined_body_type = "Endomorfo"
            else:  # IMC entre 18.5 y 24.9 (rango saludable), usamos la relación para afinar
                if relacion_hombro_cadera_simple > 1.05:
                    determined_body_type = "Mesomorfo"
                elif relacion_hombro_cadera_simple < 0.95:
                    determined_body_type = "Endomorfo"
                else:  # Relación entre 0.95 y 1.05
                    determined_body_type = "Ectomorfo"
            print(
                f"DEBUG: Tipo de cuerpo clasificado como: {determined_body_type} (IMC: {imc_valor}, Relación H/C: {relacion_hombro_cadera_simple:.2f})")
        else:
            if not is_photo_data_available_and_valid:
                print("DEBUG: Datos de fotos no válidos o insuficientes para clasificación.")
            if not is_imc_data_available_and_valid:
                print("DEBUG: Datos de peso/estatura (IMC) no válidos o insuficientes para clasificación.")
            messages.error(request, determined_body_type)  # Mostrar el mensaje de error al usuario
            print("DEBUG: No se pudo clasificar el tipo de cuerpo debido a datos insuficientes/incorrectos.")

        # --- MODIFICADO: Creación o Actualización de MedicionCuerpo ---
        # Solo guardamos una nueva medición si se proporcionaron datos de fotos O si se actualizaron peso/estatura
        # y no se procesaron fotos (para evitar duplicados o mediciones vacías)

        # Criterio para crear una NUEVA MedicionCuerpo:
        # Se proporcionaron y procesaron fotos (aunque la clasificación pueda fallar)
        if body_photos_data:  # Implica un intento de nueva medición con fotos
            MedicionCuerpo.objects.create(
                usuario=request.user,
                peso=peso_kg,
                estatura=estatura_cm,
                ancho_hombros=promedio_ancho_hombros,
                ancho_caderas=promedio_ancho_caderas,
                icc_estimado=imc_valor,  # Guardar IMC aquí
                relacion_hombro_cintura=relacion_hombro_cadera_simple,
                tipo_cuerpo=determined_body_type,  # El tipo de cuerpo final o el mensaje de error
                body_photos_data=json.dumps(body_photos_data),
                fecha_medicion=datetime.now()  # Fecha de la nueva medición
            )
            messages.success(request,
                             "Medición corporal registrada exitosamente." if determined_body_type != "No se pudo establecer el tipo de cuerpo, datos insuficientes o en posición INCORRECTA" else determined_body_type)
            print("DEBUG: Nueva MedicionCuerpo creada con datos de foto.")

        # Criterio para ACTUALIZAR la última MedicionCuerpo existente (si no se proporcionaron fotos)
        # Solo si hay una última medición y se cambió el peso o la estatura
        elif ultima_medicion and ((peso_kg is not None and ultima_medicion.peso != peso_kg) or \
                                  (estatura_cm is not None and ultima_medicion.estatura != estatura_cm)):
            ultima_medicion.peso = peso_kg if peso_kg is not None else ultima_medicion.peso
            ultima_medicion.estatura = estatura_cm if estatura_cm is not None else ultima_medicion.estatura
            ultima_medicion.icc_estimado = imc_valor  # Actualizar IMC
            ultima_medicion.relacion_hombro_cintura = relacion_hombro_cadera_simple  # Actualizar relación si se recalcula
            ultima_medicion.tipo_cuerpo = determined_body_type  # Actualizar el tipo de cuerpo o mensaje de error
            ultima_medicion.fecha_medicion = datetime.now()  # Actualizar la fecha de modificación
            ultima_medicion.save(
                update_fields=['peso', 'estatura', 'icc_estimado', 'relacion_hombro_cintura', 'tipo_cuerpo',
                               'fecha_medicion'])
            messages.success(request,
                             "Peso y/o estatura actualizados en la última medición." if determined_body_type != "No se pudo establecer el tipo de cuerpo, datos insuficientes o en posición INCORRECTA" else determined_body_type)
            print("DEBUG: Última MedicionCuerpo actualizada (solo peso/estatura).")

        # Mensaje si no hubo datos significativos para guardar/actualizar
        elif not body_photos_data and peso_kg is None and estatura_cm is None:
            messages.warning(request,
                             "No se proporcionaron fotos ni datos de peso/estatura para registrar una medición.")
            print("DEBUG: No se proporcionaron datos para nueva medición ni actualización.")

        # --- MODIFICADO: Manejo de UserProfileForm ---
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil de usuario actualizado exitosamente.")
        else:
            messages.error(request, "Hubo un error al guardar el perfil. Por favor, revisa los datos.")
            print("ERRORES DEL FORMULARIO UserProfileForm:", form.errors)

    # --- MODIFICADO: Obtener la última medición de nuevo para el contexto (después de cualquier guardado) ---
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    # --- El resto del contexto se mantiene igual ---
    body_photos_for_template = []
    if ultima_medicion and ultima_medicion.body_photos_data:
        try:
            body_photos_for_template = json.loads(ultima_medicion.body_photos_data)
        except json.JSONDecodeError:
            print("ERROR: No se pudo decodificar el JSON de las fotos de cuerpo para el template.")
            body_photos_for_template = []

    context = {
        'form': form,
        'ultima_medicion': ultima_medicion,
        'body_photos_for_template': body_photos_for_template,
        'is_authenticated_user': request.user.is_authenticated,
    }
    return render(request, 'perfil/perfil.html', context)