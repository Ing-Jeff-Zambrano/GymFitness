from django.urls import path
from . import views
app_name = 'progreso'
urlpatterns = [
    path('', views.index, name='progreso_home'),
]
