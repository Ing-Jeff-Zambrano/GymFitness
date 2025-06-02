from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from .forms import SignUpForm, LoginForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
import json
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth import login
from datetime import date, datetime

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
            user.fecha_nacimiento = date.today()  # Establecer la fecha actual como predeterminada
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
    return render(request, 'perfil/dashboard.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def perfil(request):
    user = request.user
    if request.method == 'POST':
        # Procesar la foto de perfil subida desde la cámara
        camera_photo_data = request.POST.get('camera_photo_data')
        if camera_photo_data:
            try:
                format, imgstr = camera_photo_data.split(';base64,')
                ext = format.split('/')[-1]
                image = ContentFile(base64.b64decode(imgstr), name='camera_photo.' + ext)
                user.foto_perfil = image
                messages.success(request, 'Foto de perfil actualizada desde la cámara.')
            except Exception as e:
                messages.error(request, f'Error al guardar la foto de la cámara: {e}')

        # Procesar otros campos del perfil
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.direccion = request.POST.get('direccion', user.direccion)
        user.telefono = request.POST.get('telefono', user.telefono)
        fecha_nacimiento_str = request.POST.get('fecha_nacimiento')
        sexo = request.POST.get('sexo')
        user.ciudad = request.POST.get('ciudad', user.ciudad)
        user.pais = request.POST.get('pais', user.pais)
        user.peso = request.POST.get('peso', user.peso)
        user.estatura = request.POST.get('estatura', user.estatura)

        if fecha_nacimiento_str:
            try:
                user.fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Formato de fecha de nacimiento inválido.')
                return redirect('perfil')

        if sexo in ['M', 'F', 'O']:
            user.sexo = sexo
        else:
            messages.error(request, 'Selección de sexo inválida.')
            return redirect('perfil')

        user.save()
        messages.success(request, 'Perfil actualizado exitosamente.')
        return redirect('perfil')
    else:
        return render(request, 'perfil/perfil.html')