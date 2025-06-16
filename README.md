Proyecto Gym Fitness: Análisis de Postura y Seguimiento de Progreso
Este proyecto es una aplicación web desarrollada con Django que permite a los usuarios subir videos de sus rutinas de ejercicio para análisis de postura. Adicionalmente, ofrece herramientas para el seguimiento de progreso corporal, incluyendo mediciones, cálculo del tipo de cuerpo y visualización del historial de peso.

Integrantes:
Jefferson Zambrano
Marlon Aguiño
Jonathan Perez

🌟 Características Principales
Autenticación de Usuarios: Registro y login de usuarios para una experiencia personalizada.

Perfiles de Usuario: Gestión de información personal y seguimiento del progreso.

Subida de Videos: Interfaz intuitiva para subir videos de ejercicios.

Análisis de Postura con IA:

Detección de puntos clave del cuerpo con MediaPipe.

Cálculo de ángulos y distancias críticas para cada ejercicio.

Conteo de repeticiones (total y con buena forma).

Cálculo de porcentaje de efectividad.

Feedback en tiempo real (o post-análisis) sobre la técnica y posibles errores.

Módulo de Progreso Corporal:

Mediciones Corporales Automatizadas: Uso de visión por computadora (CV2) para la toma de medidas como el ancho de hombros y caderas a partir de imágenes.

Cálculo del Tipo de Cuerpo (Somatotipo): Determinación del biotipo del usuario (Ectomorfo, Mesomorfo, Endomorfo) basado en mediciones corporales, peso y estatura.

Historial de Peso Interactivo: Visualización dinámica del historial de peso del usuario utilizando D3.js para un seguimiento claro del progreso.

Ejercicios Soportados (Análisis de Postura):

Curl de Bíceps

Extensiones de Tríceps

Press de Hombros

Elevaciones Laterales

Remo

Peso Muerto

Press de Banca

Apertura con Mancuerna

Previsualización de Video: Permite al usuario ver el video subido directamente en la interfaz.

Gestión de Medios: Almacenamiento temporal de videos para análisis y limpieza posterior.

🚀 Tecnologías Utilizadas
Backend:

Python 3.x

Django (Framework Web)

OpenCV (CV2 - Visión por Computadora para análisis y mediciones corporales)

MediaPipe (Detección de Pose con IA)

NumPy (Cálculos numéricos)

Frontend:

HTML5

CSS3 (Tailwind CSS para utilidades y responsive design)

JavaScript (para interacciones asíncronas y subida de archivos)

D3.js (para visualización de datos de progreso)

Bootstrap (para el layout general de la plantilla base, si aplica)

Base de Datos: SQLite3 (para desarrollo, configurable para PostgreSQL en producción)

Control de Versiones: Git / GitHub

🛠️ Configuración y Ejecución del Proyecto
Sigue estos pasos para poner el proyecto en marcha en tu entorno local:

1. Clonar el Repositorio
git clone <https://github.com/Ing-Jeff-Zambrano/GymFitness.git>
cd Gym_Fitness # O el nombre de la carpeta raíz de tu proyecto

2. Crear y Activar un Entorno Virtual
Es altamente recomendado usar un entorno virtual para gestionar las dependencias del proyecto.

Windows (CMD/PowerShell):

python -m venv .venv
.venv\Scripts\activate

macOS/Linux (Bash/Zsh):

python3 -m venv .venv
source .venv/bin/activate

3. Instalar Dependencias
Con el entorno virtual activado, instala las librerías necesarias desde requirements.txt:

pip install -r requirements.txt

4. Realizar Migraciones de la Base de Datos
Django necesita que apliques las migraciones para crear la estructura de la base de datos:

python manage.py migrate

5. Crear un Superusuario (Opcional, pero recomendado para el panel de administración)
Para acceder al panel de administración de Django y gestionar usuarios/datos:

python manage.py createsuperuser

Sigue las instrucciones en pantalla para crear el usuario.

6. Ejecutar el Servidor de Desarrollo
Ahora puedes iniciar el servidor web de Django:

python manage.py runserver

7. Acceder a la Aplicación
Abre tu navegador web y visita:

Aplicación principal: http://127.0.0.1:8000/ (Serás redirigido al login).

Análisis de Postura: http://127.0.0.1:8000/analisis-postura/analizar-video/

Seguimiento de Progreso: http://127.0.0.1:8000/progreso/ (O la URL que hayas configurado para el módulo de progreso)

Panel de Administración de Django: http://127.0.0.1:8000/admin/

📊 Uso de la Aplicación
Análisis de Postura:
Regístrate o Inicia Sesión.

Navega a la sección de Análisis de Postura.

Selecciona el ejercicio que deseas analizar.

Haz clic en "Introducir Video" y selecciona un archivo de video local (.mp4, .mov, etc.).

Haz clic en "Validar Ejercicio".

El sistema procesará el video y te mostrará los resultados (repeticiones, efectividad, feedback) y una previsualización del video.

Seguimiento de Progreso:
Regístrate o Inicia Sesión.

Navega a la sección de Progreso.

Aquí podrás introducir tus mediciones (peso, estatura, y si la interfaz lo permite, subir fotos para el cálculo de ancho de hombros/caderas).

El sistema calculará y mostrará tu tipo de cuerpo.

Podrás ver una gráfica interactiva de tu historial de peso a lo largo del tiempo, generada con D3.js.

📁 Estructura del Proyecto
Gym_Fitness/
├── Gym_Fitness_Project/         # Configuración principal de Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── nutricion/                   # Aplicación Django para análisis de postura
│   ├── migrations/
│   ├── templates/
│   │   └── nutricion/
│   │       └── upload.html      # Plantilla principal para subir videos
│   ├── analysis_logic.py        # Lógica de análisis de video (MediaPipe, OpenCV)
│   ├── urls.py
│   └── views.py
├── perfil/                      # Aplicación Django para perfiles de usuario y autenticación
│   ├── models.py
│   ├── views.py
│   └── ...
├── progreso/                    # Aplicación Django para el seguimiento del progreso y mediciones
│   ├── migrations/
│   ├── templates/
│   │   └── progreso/
│   │       └── index.html       # Plantilla principal para mediciones y historial
│   ├── urls.py
│   ├── views.py
│   ├── models.py                # Modelos para guardar mediciones y tipo de cuerpo
│   └── body_measurement.py      # Lógica para cálculo de ancho de hombros/caderas (CV2) y somatotipo
├── static/                      # Archivos estáticos (CSS, JS, imágenes de referencia)
│   ├── assets/
│   │   ├── css/
│   │   ├── img/                 # Imágenes de los ejercicios (1.PNG, 2.PNG, etc.)
│   │   └── js/                  # Scripts JS, incluyendo D3.js
├── media/                       # Archivos subidos por los usuarios (fotos de perfil, videos temporales)
│   ├── perfil_pics/
│   ├── temp_videos/
├── templates/                   # Plantillas base compartidas
│   └── includes/
│   └── layouts/
├── manage.py                    # Utilidad de línea de comandos de Django
├── requirements.txt             # Lista de dependencias del proyecto
└── README.md                    # Este archivo
└── .gitignore                   # Archivo para ignorar archivos y carpetas en Git



📄 Licencia
Este proyecto está bajo la licencia de Software Total. 