from django.urls import path
from . import views

urlpatterns = [
    path('', views.nutricion_view, name='nutricion_home'),
]