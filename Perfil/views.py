from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from .forms import SignUpForm, LoginForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
import json
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth import login
from .models import Usuario, MedicionCuerpo
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import io
from PIL import Image
import numpy as np
import cv2
import mediapipe as mp

User = get_user_model()


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
                return render(request, 'perfil/login.html', {'form': form, 'error': 'Invalid username or password'})
        else:
            return render(request, 'perfil/login.html', {'form': form, 'error': 'Invalid form'})
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
    else:
        form = SignUpForm()
    return render(request, 'perfil/register.html', {"form": form, "msg": msg, "success": success})


@login_required
def dashboard(request):
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()
    tipo_cuerpo = ultima_medicion.tipo_cuerpo if ultima_medicion else "No determinado"
    context = {
        'tipo_cuerpo': tipo_cuerpo,
    }
    return render(request, 'perfil/dashboard.html', context)


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def perfil(request):
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    if request.method == 'POST':
        files_data = request.FILES.copy()

        camera_photo_data = request.POST.get('camera_photo_data')
        if camera_photo_data:
            try:
                format, imgstr = camera_photo_data.split(';base64,')
                ext = format.split('/')[-1]
                data = base64.b64decode(imgstr)
                file_name = f"profile_pic_{request.user.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                files_data['foto_perfil'] = ContentFile(data, name=file_name)
            except Exception as e:
                print(f"Error al procesar la foto de la cámara (Base64): {e}")
                messages.error(request, "Hubo un error al procesar la foto de la cámara.")

        form = UserProfileForm(request.POST, files_data, instance=request.user)

        # --- MODIFICACIÓN AQUÍ: Manejar cadenas vacías para peso y estatura ---
        peso_input_str = request.POST.get('peso')
        estatura_input_str = request.POST.get('estatura')

        # Convertir a float solo si la cadena no está vacía y es un número válido
        peso_kg = None
        if peso_input_str and peso_input_str.strip() != '':  # Asegura que no sea solo espacios
            try:
                peso_kg = float(peso_input_str)
            except ValueError:
                messages.error(request, "El peso ingresado no es un número válido.")
                peso_kg = None  # Asegurarse de que sea None si hay error

        estatura_cm = None
        if estatura_input_str and estatura_input_str.strip() != '':  # Asegura que no sea solo espacios
            try:
                estatura_cm = float(estatura_input_str)
            except ValueError:
                messages.error(request, "La estatura ingresada no es un número válido.")
                estatura_cm = None  # Asegurarse de que sea None si hay error
        # --- FIN DE MODIFICACIÓN ---

        if peso_kg is not None or estatura_cm is not None or request.POST.get('body_photo_1'):
            medicion_data = {
                'usuario': request.user,
                'peso': peso_kg,
                'estatura': estatura_cm,
                'ancho_hombros': None,
                'ancho_caderas': None,
                'icc_estimado': None,
                'relacion_hombro_cintura': None,
                'tipo_cuerpo': None,
            }

            body_photos_data = []
            for i in range(1, 11):
                image_data_url = request.POST.get(f'body_photo_{i}')
                if image_data_url:
                    body_photos_data.append(image_data_url)

            if body_photos_data:
                hombros_anchos = []
                caderas_anchas = []

                for image_data in body_photos_data:
                    landmarks, ancho, alto = procesar_imagen_tipo_cuerpo(image_data)
                    if landmarks:
                        lm_hombro_izq = landmarks[11]
                        lm_hombro_der = landmarks[12]
                        lm_cadera_izq = landmarks[23]
                        lm_cadera_der = landmarks[24]

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

                promedio_ancho_hombros = sum(hombros_anchos) / len(hombros_anchos) if hombros_anchos else None
                promedio_ancho_caderas = sum(caderas_anchas) / len(caderas_anchas) if caderas_anchas else None

                icc_estimado = None
                relacion_hombro_cintura = promedio_ancho_hombros / (
                            promedio_ancho_caderas * 0.9) if promedio_ancho_caderas and promedio_ancho_hombros else None
                tipo_cuerpo_estimado = "No se pudo determinar"

                if promedio_ancho_hombros is not None and promedio_ancho_caderas is not None:
                    proporcion_hombro_cadera_simple = promedio_ancho_hombros / promedio_ancho_caderas if promedio_ancho_caderas else None
                    if proporcion_hombro_cadera_simple is not None:
                        if proporcion_hombro_cadera_simple > 1.05:
                            tipo_cuerpo_estimado = "Mesomorfo (tendencia)"
                        elif proporcion_hombro_cadera_simple < 0.95:
                            tipo_cuerpo_estimado = "Endomorfo (tendencia)"
                        else:
                            tipo_cuerpo_estimado = "Ectomorfo o mezcla"

                medicion_data['ancho_hombros'] = promedio_ancho_hombros
                medicion_data['ancho_caderas'] = promedio_ancho_caderas
                medicion_data['icc_estimado'] = icc_estimado
                medicion_data['relacion_hombro_cintura'] = relacion_hombro_cintura
                medicion_data['tipo_cuerpo'] = tipo_cuerpo_estimado

            MedicionCuerpo.objects.create(**medicion_data)
            messages.success(request, "Medición corporal registrada exitosamente.")
            ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

        if form.is_valid():
            user = form.save()
            messages.success(request, "Perfil actualizado exitosamente.")
            return redirect('perfil')
        else:
            messages.error(request, "Hubo un error al guardar el perfil. Por favor, revisa los datos.")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'perfil/perfil.html', {'form': form, 'ultima_medicion': ultima_medicion})


mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils


def procesar_imagen_tipo_cuerpo(image_data_url):
    try:
        image_str = image_data_url.split(',')[1]
        image_bytes = base64.b64decode(image_str)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img_array = np.array(image)
        img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        alto, ancho, _ = img_cv2.shape
        resultados = pose.process(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))
        if resultados.pose_landmarks:
            landmarks = resultados.pose_landmarks.landmark
            return landmarks, ancho, alto
        else:
            return None, ancho, alto
    except Exception as e:
        print(f"Error al procesar la imagen: {e}")
        return None, None, None