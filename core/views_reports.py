from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from citas.models import Cita, EstadoCita
from especialidades.models import Especialidad

Usuario = get_user_model()


# ─── API ─────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAdminUser])
def reportes_api(request):
    desde = request.query_params.get('desde')
    hasta = request.query_params.get('hasta')

    citas = Cita.objects.select_related('estado', 'medico__usuario', 'horario')
    if desde:
        citas = citas.filter(horario__fecha__gte=desde)
    if hasta:
        citas = citas.filter(horario__fecha__lte=hasta)

    # Citas por estado
    estados = citas.values('estado__nombre').annotate(total=Count('id')).order_by('estado__nombre')

    # Citas por especialidad
    por_especialidad = (
        citas.values('medico__especialidades__especialidad__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    # Tasa de no asistencia por médico
    no_asistio = EstadoCita.objects.get(nombre='no_asistio').pk
    cancelada = EstadoCita.objects.get(nombre='cancelada').pk

    medicos_tasa = (
        citas.values(
            'medico__id', 'medico__usuario__nombre', 'medico__usuario__apellido'
        )
        .annotate(
            total=Count('id'),
            no_asistieron=Count('id', filter=Q(estado=no_asistio)),
            canceladas=Count('id', filter=Q(estado=cancelada)),
        )
        .order_by('medico__usuario__apellido')
    )

    return Response({
        'resumen': {
            'total_citas': citas.count(),
            'total_pacientes': Usuario.objects.filter(rol='paciente', is_active=True).count(),
            'total_medicos': Usuario.objects.filter(rol='medico', is_active=True).count(),
        },
        'por_estado': list(estados),
        'por_especialidad': list(por_especialidad),
        'tasa_no_asistencia': list(medicos_tasa),
    })


# ─── Frontend ────────────────────────────────────────────────────────────────

@login_required
def reportes(request):
    if not request.user.is_staff:
        return render(request, 'core/sin_permiso.html', status=403)

    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')

    citas = Cita.objects.select_related('estado', 'medico__usuario', 'horario')
    if desde:
        citas = citas.filter(horario__fecha__gte=desde)
    if hasta:
        citas = citas.filter(horario__fecha__lte=hasta)

    estados = citas.values('estado__nombre').annotate(total=Count('id')).order_by('estado__nombre')

    por_especialidad = (
        citas.values('medico__especialidades__especialidad__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    no_asistio = EstadoCita.objects.get(nombre='no_asistio').pk
    cancelada = EstadoCita.objects.get(nombre='cancelada').pk

    medicos_tasa = (
        citas.values(
            'medico__id', 'medico__usuario__nombre', 'medico__usuario__apellido'
        )
        .annotate(
            total=Count('id'),
            no_asistieron=Count('id', filter=Q(estado=no_asistio)),
            canceladas=Count('id', filter=Q(estado=cancelada)),
        )
        .order_by('medico__usuario__apellido')
    )

    return render(request, 'core/reportes.html', {
        'desde': desde,
        'hasta': hasta,
        'resumen': {
            'total_citas': citas.count(),
            'total_pacientes': Usuario.objects.filter(rol='paciente', is_active=True).count(),
            'total_medicos': Usuario.objects.filter(rol='medico', is_active=True).count(),
            'total_especialidades': Especialidad.objects.filter(activo=True).count(),
        },
        'por_estado': estados,
        'por_especialidad': por_especialidad,
        'medicos_tasa': medicos_tasa,
    })
