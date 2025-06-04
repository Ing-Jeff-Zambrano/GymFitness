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
from django.core.files.base import ContentFile  # Asegúrate de que esta importación esté aquí

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
            imc_calculado_para_medicion = round(float(medicion.peso) / (estatura_m ** 2), 2)
        medicion.imc_valor = imc_calculado_para_medicion  # Adjuntar el IMC calculado al objeto

    context = {
        'tipo_cuerpo': tipo_cuerpo,
        'ultima_medicion': ultima_medicion,
        'mediciones_recientes': mediciones_recientes,  # <-- PASAMOS ESTO AL CONTEXTO DEL DASHBOARD
    }
    return render(request, 'perfil/dashboard.html', context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def perfil(request):
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    form = UserProfileForm(instance=request.user)

    if request.method == 'POST':
        files_data = request.FILES.copy()

        camera_photo_data = request.POST.get('camera_photo_data')
        if camera_photo_data:
            try:
                format, imgstr = camera_photo_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'{request.user.username}_perfil.{ext}')

                files_data['foto_perfil'] = data
                messages.success(request, "Foto de perfil capturada y lista para guardar.")
                print("DEBUG: Foto de perfil base64 procesada y añadida a files_data.")
            except Exception as e:
                print(f"Error al procesar la foto de la cámara (Base64): {e}")
                messages.error(request, "Hubo un error al procesar la foto de la cámara.")

        form = UserProfileForm(request.POST, files_data, instance=request.user)

        peso_input_str = request.POST.get('peso')
        estatura_input_str = request.POST.get('estatura')

        peso_kg = None
        if peso_input_str and peso_input_str.strip() != '':
            try:
                peso_kg = float(peso_input_str)
            except ValueError:
                messages.error(request, "El peso ingresado no es un número válido.")

        estatura_cm = None
        if estatura_input_str and estatura_input_str.strip() != '':
            try:
                estatura_cm = float(estatura_input_str)
            except ValueError:
                messages.error(request, "La estatura ingresada no es un número válido.")

        body_photos_data = []
        measurement_photo_data_json = request.POST.get('measurement_photo_data')

        new_measurement_processed = False

        if measurement_photo_data_json and json.loads(measurement_photo_data_json):
            print("DEBUG: Se detectaron fotos de medición. Creando una NUEVA MedicionCuerpo.")
            try:
                body_photos_data = json.loads(measurement_photo_data_json)
                print(f"DEBUG: Recibidas {len(body_photos_data)} fotos para detección de cuerpo.")
            except json.JSONDecodeError as e:
                print(f"ERROR: No se pudo decodificar el JSON de las fotos de medición: {e}")
                messages.error(request, "Error al procesar los datos de las fotos de medición.")
                body_photos_data = []

            if body_photos_data:
                hombros_anchos = []
                caderas_anchas = []

                for i, image_data_url in enumerate(body_photos_data):
                    print(f"DEBUG: Procesando foto de medición {i + 1}...")
                    landmarks, ancho, alto = procesar_imagen_tipo_cuerpo(image_data_url)

                    if landmarks:
                        lm_hombro_izq = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                        lm_hombro_der = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
                        lm_cadera_izq = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
                        lm_cadera_der = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

                        min_conf_deteccion = 0.7
                        if lm_hombro_izq.visibility > min_conf_deteccion and \
                                lm_hombro_der.visibility > min_conf_deteccion and \
                                lm_cadera_izq.visibility > min_conf_deteccion and \
                                lm_cadera_der.visibility > min_conf_deteccion:

                            hombro_izquierdo_px = int(lm_hombro_izq.x * ancho)
                            hombro_derecho_px = int(lm_hombro_der.x * ancho)
                            ancho_hombros_px = abs(hombro_derecho_px - hombro_izquierdo_px)
                            hombros_anchos.append(ancho_hombros_px)

                            cadera_izquierda_px = int(lm_cadera_izq.x * ancho)
                            cadera_derecha_px = int(lm_cadera_der.x * ancho)
                            ancho_caderas_px = abs(cadera_derecha_px - cadera_izquierda_px)
                            caderas_anchas.append(ancho_caderas_px)
                            print(
                                f"DEBUG: Foto {i + 1} - Hombros detectados: {ancho_hombros_px:.2f}px, Caderas detectadas: {ancho_caderas_px:.2f}px")
                        else:
                            print(
                                f"DEBUG: Foto {i + 1} - Visibilidad de landmarks clave baja. Saltando esta foto para cálculo de medidas.")
                    else:
                        print(
                            f"DEBUG: Foto {i + 1} - No se detectaron landmarks. Saltando esta foto para cálculo de medidas.")

                promedio_ancho_hombros = sum(hombros_anchos) / len(hombros_anchos) if hombros_anchos else None
                promedio_ancho_caderas = sum(caderas_anchas) / len(caderas_anchas) if caderas_anchas else None

                print(
                    f"DEBUG: Promedio Ancho Hombros: {promedio_ancho_hombros}, Promedio Ancho Caderas: {promedio_ancho_caderas}")

                medicion_data = {
                    'usuario': request.user,
                    'peso': peso_kg,
                    'estatura': estatura_cm,
                    'ancho_hombros': promedio_ancho_hombros,
                    'ancho_caderas': promedio_ancho_caderas,
                    'icc_estimado': None,
                    'relacion_hombro_cintura': None,
                    'tipo_cuerpo': "No determinado",
                    'body_photos_data': json.dumps(body_photos_data),
                }

                if promedio_ancho_hombros is not None and promedio_ancho_caderas is not None and promedio_ancho_caderas > 0:
                    relacion_hombro_cadera_simple = promedio_ancho_hombros / promedio_ancho_caderas
                    medicion_data['relacion_hombro_cintura'] = relacion_hombro_cadera_simple

                    if relacion_hombro_cadera_simple > 1.05:
                        medicion_data['tipo_cuerpo'] = "Mesomorfo"
                    elif relacion_hombro_cadera_simple < 0.95:
                        medicion_data['tipo_cuerpo'] = "Endomorfo"
                    else:
                        medicion_data['tipo_cuerpo'] = "Ectomorfo"

                    print(
                        f"DEBUG: Tipo de cuerpo estimado: {medicion_data['tipo_cuerpo']} (Relación Hombro/Cadera: {relacion_hombro_cadera_simple:.2f})")
                else:
                    print("DEBUG: No hay suficientes datos de hombros/caderas para calcular el tipo de cuerpo.")
                    medicion_data['tipo_cuerpo'] = "No determinado (datos insuficientes)"

                MedicionCuerpo.objects.create(**medicion_data)
                messages.success(request, "Medición corporal registrada exitosamente.")
                new_measurement_processed = True
            else:
                messages.warning(request,
                                 "Se inició la detección de cuerpo, pero no se recibieron fotos válidas para el cálculo.")

        elif (peso_kg is not None or estatura_cm is not None) and not new_measurement_processed:
            print(
                "DEBUG: No se detectaron fotos de medición, pero sí peso/estatura. Actualizando o creando MedicionCuerpo.")
            if ultima_medicion:
                print("DEBUG: Última medición existente encontrada. Verificando cambios en peso/estatura.")
                if (peso_kg is not None and ultima_medicion.peso != peso_kg) or \
                        (estatura_cm is not None and ultima_medicion.estatura != estatura_cm):
                    ultima_medicion.peso = peso_kg if peso_kg is not None else ultima_medicion.peso
                    ultima_medicion.estatura = estatura_cm if estatura_cm is not None else ultima_medicion.estatura
                    ultima_medicion.save(update_fields=['peso', 'estatura'])
                    messages.success(request, "Peso y/o estatura actualizados en la última medición.")
                    print("DEBUG: Peso y/o estatura actualizados en la última medición existente.")
                else:
                    print("DEBUG: Peso y estatura no cambiaron en la última medición. No se guardó en MedicionCuerpo.")
            else:
                print("DEBUG: No hay mediciones existentes. Creando nueva medición solo con peso/estatura.")
                MedicionCuerpo.objects.create(
                    usuario=request.user,
                    peso=peso_kg,
                    estatura=estatura_cm,
                    tipo_cuerpo="No determinado (solo peso/estatura)",
                    body_photos_data="[]"
                )
                messages.success(request, "Nueva medición creada con peso y/o estatura.")

        if form.is_valid():
            print("DEBUG: UserProfileForm es válido. Intentando guardar...")
            form.save()
            print("DEBUG: UserProfileForm guardado.")
            messages.success(request, "Perfil actualizado exitosamente.")
        else:
            print("DEBUG: UserProfileForm NO ES VÁLIDO.")
            print("ERRORES DEL FORMULARIO:", form.errors)
            messages.error(request, "Hubo un error al guardar el perfil. Por favor, revisa los datos.")

    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

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
    }
    return render(request, 'perfil/perfil.html', context)