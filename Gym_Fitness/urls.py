from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Importa settings
from django.conf.urls.static import static # Importa static

# Asegúrate de importar login_view si lo usas directamente aquí
from perfil.views import login_view # Asumiendo que login_view está en perfil/views.py

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_view, name='login'),
    path('perfil/', include('perfil.urls')),
    path('progreso/', include('progreso.urls')),
    path('analisis-postura/', include('nutricion.urls', namespace='analisis_postura')),
]

# ESTAS LÍNEAS SON FUNDAMENTALES PARA SERVIR ARCHIVOS MEDIA EN DESARROLLO
# Y DEBEN ESTAR DENTRO DE LA CONDICIÓN DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
