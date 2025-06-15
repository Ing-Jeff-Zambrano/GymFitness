from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from perfil.models import MedicionCuerpo  # Importa el modelo MedicionCuerpo
import json  # Necesario para json.dumps


@login_required
def index(request):  # O el nombre que tenga tu vista de progreso (ej. progreso_view)
    # Obtener TODAS las mediciones del cuerpo para el usuario actual, ordenadas por fecha_medicion
    mediciones_completas = MedicionCuerpo.objects.filter(usuario=request.user).order_by('fecha_medicion')

    # --- PREPARAR DATOS PARA EL GRÁFICO D3.JS (Progreso de Peso) ---
    # El gráfico D3.js espera una lista de objetos: [{ 'fecha': 'YYYY-MM-DD', 'peso': X.X }, ...]
    data_peso_para_chart = []

    # También preparamos datos para otros gráficos (IMC con Chart.js) y la tabla
    fechas_chart = []  # Para el eje X de Chart.js
    imcs_chart = []  # Para el gráfico IMC de Chart.js

    # Iterar sobre todas las mediciones para preparar los datos
    for med in mediciones_completas:
        # Para el gráfico de Peso D3.js
        if med.peso is not None and med.fecha_medicion is not None:
            data_peso_para_chart.append({
                'fecha': med.fecha_medicion.strftime('%Y-%m-%d'),  # Formato de fecha esperado por D3.js
                'peso': float(med.peso)
            })

        # Para el gráfico de IMC (Chart.js): fechas e IMC
        fechas_chart.append(med.fecha_medicion.strftime('%Y-%m-%d'))

        imc_calculado_para_medicion = None
        if med.peso is not None and med.estatura is not None and med.estatura > 0:
            estatura_m = float(med.estatura) / 100.0
            if estatura_m > 0:  # Evitar división por cero
                imc_calculado_para_medicion = round(float(med.peso) / (estatura_m ** 2), 2)

        imcs_chart.append(imc_calculado_para_medicion)
        # Adjuntar el IMC calculado a la instancia de la medición para usarlo directamente en la tabla HTML
        med.imc_valor = imc_calculado_para_medicion

    # Convertir la lista de objetos para el gráfico de peso a una cadena JSON
    fechas_pesos_json = json.dumps(data_peso_para_chart, default=str)

    # Convertir las listas para el gráfico de IMC a cadenas JSON
    fechas_json = json.dumps(fechas_chart)
    imcs_json = json.dumps(imcs_chart)

    # Obtener la última medición para las métricas clave (tarjetas superiores y tipo de cuerpo)
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    # Calcular el IMC para la última medición si existe (para la tarjeta superior)
    imc_ultima_medicion = None
    if ultima_medicion and ultima_medicion.peso is not None and ultima_medicion.estatura is not None and ultima_medicion.estatura > 0:
        estatura_m = float(ultima_medicion.estatura) / 100.0
        if estatura_m > 0:  # Evitar división por cero
            imc_ultima_medicion = round(float(ultima_medicion.peso) / (estatura_m ** 2), 2)

    # Obtener el tipo de cuerpo de la última medición para la tarjeta superior
    tipo_cuerpo = "No determinado"
    if ultima_medicion and ultima_medicion.tipo_cuerpo:
        tipo_cuerpo = ultima_medicion.tipo_cuerpo

    print(f"DEBUG: En progreso/views.py, tipo_cuerpo antes de renderizar: '{tipo_cuerpo}'")

    context = {
        'ultima_medicion': ultima_medicion,
        'imc_ultima_medicion': imc_ultima_medicion,
        'tipo_cuerpo': tipo_cuerpo,  # Pasar el tipo de cuerpo para la tarjeta
        # Últimas 5 mediciones para la tabla
        'mediciones_recientes': MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion')[:5],

        # Variables JSON para los gráficos
        'fechas_pesos_json': fechas_pesos_json,  # Para D3.js (gráfico de peso)
        'fechas_json': fechas_json,  # Para Chart.js (gráfico de IMC)
        'imcs_json': imcs_json,  # Para Chart.js (gráfico de IMC)
    }
    return render(request, 'progreso/index.html', context)



