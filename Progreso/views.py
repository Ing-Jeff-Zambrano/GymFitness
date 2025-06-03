from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from perfil.models import MedicionCuerpo  # Importa el modelo MedicionCuerpo


@login_required
def index(request):
    # Obtener todas las mediciones del cuerpo para el usuario actual, ordenadas por fecha ascendente
    mediciones = MedicionCuerpo.objects.filter(usuario=request.user).order_by('fecha_medicion')

    # Preparar datos para los gráficos y calcular IMC para cada medición
    fechas = []
    pesos = []
    imcs = []

    for med in mediciones:
        fechas.append(med.fecha_medicion.strftime('%Y-%m-%d'))
        pesos.append(float(med.peso) if med.peso is not None else None)

        # Calcular IMC para la medición actual
        imc_calculado_para_medicion = None
        if med.peso is not None and med.estatura is not None and med.estatura > 0:
            estatura_m = float(med.estatura) / 100.0
            imc_calculado_para_medicion = round(float(med.peso) / (estatura_m ** 2), 2)

        imcs.append(imc_calculado_para_medicion)
        # Adjuntar el IMC calculado a la instancia de la medición para usarlo en la tabla
        med.imc_valor = imc_calculado_para_medicion

        # Vamos a obtener la última medición para las métricas clave
    ultima_medicion = MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion').first()

    # Calcular el IMC para la última medición si existe (para la tarjeta superior)
    imc_ultima_medicion = None
    if ultima_medicion and ultima_medicion.peso is not None and ultima_medicion.estatura is not None and ultima_medicion.estatura > 0:
        estatura_m = float(ultima_medicion.estatura) / 100.0
        imc_ultima_medicion = round(float(ultima_medicion.peso) / (estatura_m ** 2), 2)

    context = {
        'ultima_medicion': ultima_medicion,
        'imc_ultima_medicion': imc_ultima_medicion,  # <-- Valor para la tarjeta superior
        'mediciones_recientes': MedicionCuerpo.objects.filter(usuario=request.user).order_by('-fecha_medicion')[:5],
        # Últimas 5 mediciones para la tabla
        'fechas_json': fechas,  # Para los gráficos
        'pesos_json': pesos,  # Para los gráficos
        'imcs_json': imcs,  # Para los gráficos
    }
    return render(request, 'progreso/index.html', context)  # Asegúrate de que el nombre del template sea 'index.html'
