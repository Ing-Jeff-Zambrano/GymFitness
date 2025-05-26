from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm, LoginForm
from django.contrib.auth.decorators import login_required


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
            form.save()
            msg = 'User created - please <a href="/">login</a>.'
            success = True
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()
    return render(request, 'perfil/register.html', {"form": form, "msg": msg, "success": success})

@login_required
def dashboard(request):
    return render(request, 'perfil/dashboard.html')



@login_required
def logout(request):
    logout(request)
    return redirect('login')