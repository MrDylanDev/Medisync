from django.db import models
from django.shortcuts import render, get_object_or_404

from especialidades.models import Especialidad
from .models import Medico, Horario


def medico_list(request):
    """Public listing of doctors with optional specialty filter and search."""
    especialidad_id = request.GET.get('especialidad')
    query = request.GET.get('q', '').strip()

    medicos = Medico.objects.select_related('usuario').prefetch_related(
        'especialidades__especialidad'
    ).all()

    especialidad = None
    if especialidad_id:
        especialidad = get_object_or_404(Especialidad, pk=especialidad_id, activo=True)
        medicos = medicos.filter(especialidades__especialidad=especialidad)

    if query:
        medicos = medicos.filter(
            models.Q(usuario__nombre__icontains=query) |
            models.Q(usuario__apellido__icontains=query) |
            models.Q(especialidades__especialidad__nombre__icontains=query)
        ).distinct()

    medicos = medicos.order_by('usuario__apellido', 'usuario__nombre')

    return render(request, 'medicos/list.html', {
        'medicos': medicos,
        'especialidad_filtro': especialidad,
        'query': query,
        'especialidades': Especialidad.objects.filter(activo=True).order_by('nombre'),
    })


def medico_detail(request, pk):
    """Public doctor profile with available schedules."""
    medico = get_object_or_404(
        Medico.objects.select_related('usuario').prefetch_related(
            'especialidades__especialidad',
        ),
        pk=pk
    )

    from datetime import date
    today = date.today()
    horarios = Horario.objects.filter(
        medico=medico,
        fecha__gte=today,
        disponible=True,
    ).order_by('fecha', 'hora_inicio')[:30]

    # Group horarios by date
    horarios_por_fecha = {}
    for h in horarios:
        fecha_key = h.fecha
        if fecha_key not in horarios_por_fecha:
            horarios_por_fecha[fecha_key] = []
        horarios_por_fecha[fecha_key].append(h)

    return render(request, 'medicos/detail.html', {
        'medico': medico,
        'horarios_por_fecha': horarios_por_fecha,
    })
