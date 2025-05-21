from django.urls import path
from . import views

urlpatterns = [
    path('', views.progreso_view, name='progreso_home'),
]
