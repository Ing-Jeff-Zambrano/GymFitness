from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages

def login_view(request):
    form = AuthenticationForm()
    return render(request, 'perfil/login.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the user after successful registration
            messages.success(request, 'Account created successfully!')
            return redirect('some_dashboard_url') # Redirect to a dashboard or home page
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'perfil/register.html', context)