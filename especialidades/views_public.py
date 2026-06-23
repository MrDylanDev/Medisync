from django.shortcuts import render

from .models import Especialidad


def especialidad_list(request):
    """Public listing of active medical specialties."""
    especialidades = Especialidad.objects.filter(activo=True).order_by('nombre')
    return render(request, 'especialidades/list.html', {
        'especialidades': especialidades,
    })
