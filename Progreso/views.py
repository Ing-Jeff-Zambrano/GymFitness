from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from perfil.models import MedicionCuerpo  # Importa el modelo MedicionCuerpo
import json  # Necesario para json.dumps


@login_required
def index(request):  # O el nombre que tenga tu vista de progreso (ej. progreso_view)
    # Obtener TODAS las mediciones del cuerpo para el usuario actual, ordenadas por fecha_medicion
    mediciones_completas = MedicionCuerpo.objects.filter(usuario=request.user).order_by('fecha_medicion')

    # Preparar datos para los gráficos
    fechas_chart = []
    pesos_chart = []
    imcs_chart = []

    # Iterar sobre todas las mediciones para preparar los datos de los gráficos y la tabla
    for med in mediciones_completas:
        # Formato para Chart.js (YYYY-MM-DD)
        fechas_chart.append(med.fecha_medicion.strftime('%Y-%m-%d'))
        pesos_chart.append(float(med.peso) if med.peso is not None else None)

        # Calcular IMC para la medición actual
        imc_calculado_para_medicion = None
        if med.peso is not None and med.estatura is not None and med.estatura > 0:
            estatura_m = float(med.estatura) / 100.0
            imc_calculado_para_medicion = round(float(med.peso) / (estatura_m ** 2), 2)

        imcs_chart.append(imc_calculado_para_medicion)
        # Adjuntar el IMC calculado a la instancia de la medición para usarlo directamente en la tabla HTML
        med.imc_valor = imc_calculado_para_medicion

    # Obtener la última medición para las métricas clave (tarjetas superiores y tipo de cuerpo)
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    # Calcular el IMC para la última medición si existe (para la tarjeta superior)
    imc_ultima_medicion = None
    if ultima_medicion and ultima_medicion.peso is not None and ultima_medicion.estatura is not None and ultima_medicion.estatura > 0:
        estatura_m = float(ultima_medicion.estatura) / 100.0
        if estatura_m > 0:  # Evitar división por cero
            imc_ultima_medicion = round(float(ultima_medicion.peso) / (estatura_m ** 2), 2)

    # Obtener el tipo de cuerpo de la última medición para la tarjeta superior
    # Si no hay última medición o tipo_cuerpo es None/vacío, se asigna "No determinado"
    tipo_cuerpo = "No determinado"
    if ultima_medicion and ultima_medicion.tipo_cuerpo:
        tipo_cuerpo = ultima_medicion.tipo_cuerpo

    print(f"DEBUG: En progreso/views.py, tipo_cuerpo antes de renderizar: '{tipo_cuerpo}'")  # <-- ESTO ES CLAVE

    context = {
        'ultima_medicion': ultima_medicion,
        'imc_ultima_medicion': imc_ultima_medicion,
        'tipo_cuerpo': tipo_cuerpo,  # Pasar el tipo de cuerpo para la tarjeta
        'mediciones_recientes': MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion')[:5],
        # Últimas 5 para la tabla
        'fechas_json': json.dumps(fechas_chart),  # Para los gráficos
        'pesos_json': json.dumps(pesos_chart),  # Para los gráficos
        'imcs_json': json.dumps(imcs_chart),  # Para los gráficos
    }
    return render(request, 'progreso/index.html', context)  # Asegúrate de que la ruta de tu plantilla sea correcta
# Asegúrate de que el nombre del template sea 'index.html'
