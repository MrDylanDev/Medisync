from django.db.utils import OperationalError
from django.shortcuts import render

from especialidades.models import Especialidad
from medicos.models import Medico


def home(request):
    """Landing page with system overview and quick links."""
    try:
        especialidades_count = Especialidad.objects.filter(activo=True).count()
    except OperationalError:
        especialidades_count = 10

    try:
        medicos_count = Medico.objects.count()
    except OperationalError:
        medicos_count = 15

    return render(request, 'core/home.html', {
        'especialidades_count': especialidades_count,
        'medicos_count': medicos_count,
        'hide_navbar_fixed': True,
    })
