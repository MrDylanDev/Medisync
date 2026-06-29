from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from especialidades.models import Especialidad
from medicos.models import Medico, Horario
from core.utils import send_template_email
from .models import Cita, EstadoCita


@login_required
@require_http_methods(["GET", "POST"])
def agendar(request):
    if request.user.rol != 'paciente':
        messages.error(request, _('Solo los pacientes pueden agendar citas.'))
        return redirect('dashboard')

    paciente = request.user.paciente
    especialidad_id = request.GET.get('especialidad') or request.POST.get('especialidad')
    medico_id = request.GET.get('medico') or request.POST.get('medico')

    especialidades = Especialidad.objects.filter(activo=True).order_by('nombre')

    medicos = Medico.objects.select_related('usuario').prefetch_related(
        'especialidades__especialidad'
    ).all()
    especialidad_seleccionada = None
    if especialidad_id:
        especialidad_seleccionada = get_object_or_404(Especialidad, pk=especialidad_id, activo=True)
        medicos = medicos.filter(especialidades__especialidad=especialidad_seleccionada)
    medicos = medicos.order_by('usuario__apellido', 'usuario__nombre')

    medico_seleccionado = None
    horarios_por_fecha = {}
    if medico_id:
        medico_seleccionado = get_object_or_404(Medico, pk=medico_id)
        today = date.today()
        horarios = Horario.objects.filter(
            medico=medico_seleccionado,
            fecha__gte=today,
            disponible=True,
        ).order_by('fecha', 'hora_inicio')[:60]

        for h in horarios:
            horarios_por_fecha.setdefault(h.fecha, []).append(h)

    if request.method == 'POST':
        horario_id = request.POST.get('horario')
        motivo = request.POST.get('motivo', '').strip()

        errors = {}
        if not horario_id:
            errors['horario'] = _('Debe seleccionar un horario.')
        if not motivo:
            errors['motivo'] = _('Debe ingresar un motivo de consulta.')

        if not errors:
            horario = get_object_or_404(Horario, pk=horario_id, disponible=True)

            if Cita.objects.filter(horario=horario).exists():
                messages.error(request, _('Este horario ya no está disponible.'))
                return redirect('citas:agendar')

            with transaction.atomic():
                cita = Cita.objects.create(
                    paciente=paciente,
                    medico=horario.medico,
                    horario=horario,
                    motivo=motivo,
                )
                horario.disponible = False
                horario.save(update_fields=['disponible'])

            _send_appointment_confirmed(cita)
            messages.success(request, _('Cita agendada correctamente. Revisá tu correo.'))
            return redirect('citas:mis_citas')

        for field, msg in errors.items():
            messages.error(request, msg)

    return render(request, 'citas/book.html', {
        'especialidades': especialidades,
        'especialidad_seleccionada': especialidad_seleccionada,
        'medicos': medicos,
        'medico_seleccionado': medico_seleccionado,
        'horarios_por_fecha': horarios_por_fecha,
    })


@login_required
def mis_citas(request):
    if request.user.rol != 'paciente':
        messages.error(request, _('Solo los pacientes pueden ver sus citas.'))
        return redirect('dashboard')

    paciente = request.user.paciente
    estado_filtro = request.GET.get('estado')

    citas = Cita.objects.select_related(
        'medico__usuario', 'horario', 'estado'
    ).filter(paciente=paciente)

    if estado_filtro:
        citas = citas.filter(estado__nombre=estado_filtro)

    citas = citas.order_by('-horario__fecha', '-horario__hora_inicio')

    estados = EstadoCita.objects.all()

    return render(request, 'citas/list.html', {
        'citas': citas,
        'estados': estados,
        'estado_filtro': estado_filtro,
    })


@login_required
@require_http_methods(["POST"])
def cancelar(request, pk):
    cita = get_object_or_404(
        Cita.objects.select_related('horario', 'estado', 'paciente__usuario', 'medico__usuario'),
        pk=pk,
    )

    if cita.paciente.usuario != request.user:
        messages.error(request, _('No puedes cancelar una cita que no te pertenece.'))
        return redirect('citas:mis_citas')

    if cita.estado.nombre not in ('pendiente', 'confirmada'):
        messages.error(request, _('Solo se pueden cancelar citas pendientes o confirmadas.'))
        return redirect('citas:mis_citas')

    cita_datetime = datetime.combine(cita.horario.fecha, cita.horario.hora_inicio)
    cita_datetime = timezone.make_aware(cita_datetime) if timezone.is_naive(cita_datetime) else cita_datetime
    now = timezone.now()

    if cita_datetime - now < timedelta(hours=24):
        messages.error(
            request,
            _('No se puede cancelar la cita con menos de 24 horas de anticipación.'),
        )
        return redirect('citas:mis_citas')

    with transaction.atomic():
        cancelada = EstadoCita.objects.get(nombre='cancelada')
        cita.estado = cancelada
        cita.save(update_fields=['estado'])
        cita.horario.disponible = True
        cita.horario.save(update_fields=['disponible'])

    _send_appointment_cancelled(cita, request.user)
    messages.success(request, _('Cita cancelada correctamente.'))
    return redirect('citas:mis_citas')


def _get_especialidad(medico):
    relacion = medico.especialidades.filter(es_principal=True).first()
    if not relacion:
        relacion = medico.especialidades.first()
    return relacion.especialidad.nombre if relacion else ''


def _send_appointment_confirmed(cita):
    especialidad = _get_especialidad(cita.medico)
    context = {
        'paciente_nombre': cita.paciente.usuario.nombre_completo,
        'medico_nombre': f'Dr. {cita.medico.usuario.nombre_completo}',
        'especialidad': especialidad,
        'fecha': cita.horario.fecha.strftime('%d/%m/%Y'),
        'hora_inicio': cita.horario.hora_inicio.strftime('%H:%M'),
        'hora_fin': cita.horario.hora_fin.strftime('%H:%M'),
        'consultorio': cita.medico.informacion_consultorio or 'No especificado',
        'atencion_online': cita.medico.atencion_online,
        'motivo': cita.motivo,
    }
    send_template_email(
        subject='Cita confirmada — Medisync',
        template_name='emails/appointment_confirmed.html',
        context=context,
        recipient_list=[cita.paciente.usuario.correo],
    )


def _send_appointment_cancelled(cita, cancelled_by):
    especialidad = _get_especialidad(cita.medico)
    context = {
        'paciente_nombre': cita.paciente.usuario.nombre_completo,
        'medico_nombre': f'Dr. {cita.medico.usuario.nombre_completo}',
        'especialidad': especialidad,
        'fecha': cita.horario.fecha.strftime('%d/%m/%Y'),
        'hora_inicio': cita.horario.hora_inicio.strftime('%H:%M'),
        'hora_fin': cita.horario.hora_fin.strftime('%H:%M'),
        'cancelada_por': cancelled_by.nombre_completo,
    }
    send_template_email(
        subject='Cita cancelada — Medisync',
        template_name='emails/appointment_cancelled.html',
        context=context,
        recipient_list=[cita.paciente.usuario.correo],
    )
    send_template_email(
        subject='Cita cancelada — Medisync',
        template_name='emails/appointment_cancelled.html',
        context=context,
        recipient_list=[cita.medico.usuario.correo],
    )
