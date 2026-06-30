from django.db.utils import OperationalError
from django.shortcuts import render

from especialidades.models import Especialidad
from medicos.models import Medico, MedicoEspecialidad


def home(request):
    """Landing page with system overview and quick links."""
    try:
        especialidades = Especialidad.objects.filter(activo=True)[:6]
        especialidades_count = len(especialidades)
    except OperationalError:
        especialidades = []
        especialidades_count = 10

    try:
        medicos = Medico.objects.select_related('usuario').prefetch_related('especialidades__especialidad')[:6]
        medicos_count = Medico.objects.count()
    except OperationalError:
        medicos = []
        medicos_count = 15

    return render(request, 'core/home.html', {
        'especialidades': especialidades,
        'especialidades_count': especialidades_count,
        'medicos': medicos,
        'medicos_count': medicos_count,
        'hide_navbar_fixed': True,
    })
