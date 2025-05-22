from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm, LoginForm
def login_view(request):
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