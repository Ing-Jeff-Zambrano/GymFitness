from django.http import HttpResponse

def nutricion_view(request):
    return HttpResponse("¡Estás en el módulo de Nutrición!, le corresponde a Patucho semicrack")

