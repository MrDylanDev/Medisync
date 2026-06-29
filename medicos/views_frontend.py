from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from citas.models import Cita, EstadoCita
from .models import Medico, Horario


@login_required
@require_http_methods(["GET"])
def mis_horarios(request):
    if request.user.rol != 'medico':
        messages.error(request, _('Solo los médicos pueden gestionar horarios.'))
        return redirect('dashboard')

    medico = get_object_or_404(Medico, usuario=request.user)
    fecha_str = request.GET.get('fecha', date.today().isoformat())

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha = date.today()

    horarios = Horario.objects.filter(medico=medico, fecha=fecha).order_by('hora_inicio')

    return render(request, 'medicos/horarios.html', {
        'medico': medico,
        'fecha': fecha,
        'horarios': horarios,
    })


@login_required
@require_http_methods(["POST"])
def agregar_horario(request):
    if request.user.rol != 'medico':
        messages.error(request, _('Solo los médicos pueden gestionar horarios.'))
        return redirect('dashboard')

    medico = get_object_or_404(Medico, usuario=request.user)
    fecha_str = request.POST.get('fecha')
    hora_inicio_str = request.POST.get('hora_inicio')
    hora_fin_str = request.POST.get('hora_fin')
    duracion = request.POST.get('duracion_slot')

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
    except (ValueError, TypeError):
        messages.error(request, _('Formato de fecha u hora inválido.'))
        return redirect('medicos:mis_horarios')

    if hora_fin <= hora_inicio:
        messages.error(request, _('La hora de fin debe ser posterior a la de inicio.'))
        return redirect('medicos:mis_horarios')

    if duracion:
        try:
            duracion = int(duracion)
        except (TypeError, ValueError):
            duracion = 30
        if duracion not in (15, 20, 30):
            duracion = 30

        start = datetime.combine(fecha, hora_inicio)
        end = datetime.combine(fecha, hora_fin)
        delta = timedelta(minutes=duracion)
        creados = 0
        current = start
        while current + delta <= end:
            _, created = Horario.objects.get_or_create(
                medico=medico, fecha=fecha,
                hora_inicio=current.time(),
                hora_fin=(current + delta).time(),
                defaults={'disponible': True},
            )
            if created:
                creados += 1
            current += delta
        messages.success(request, _(f'Se crearon {creados} horarios.'))
    else:
        try:
            Horario.objects.create(
                medico=medico, fecha=fecha,
                hora_inicio=hora_inicio, hora_fin=hora_fin,
            )
            messages.success(request, _('Horario creado correctamente.'))
        except IntegrityError:
            messages.error(request, _('Ese horario ya existe.'))

    return redirect(f'/medicos/mis-horarios/?fecha={fecha}')


@login_required
@require_http_methods(["POST"])
def eliminar_horario(request, pk):
    if request.user.rol != 'medico':
        messages.error(request, _('Solo los médicos pueden gestionar horarios.'))
        return redirect('dashboard')

    horario = get_object_or_404(Horario, pk=pk, medico__usuario=request.user)
    fecha = horario.fecha
    horario.delete()
    messages.success(request, _('Horario eliminado.'))
    return redirect(f'/medicos/mis-horarios/?fecha={fecha}')


@login_required
@require_http_methods(["GET"])
def citas_agendadas(request):
    if request.user.rol != 'medico':
        messages.error(request, _('Solo los médicos pueden ver sus citas.'))
        return redirect('dashboard')

    medico = get_object_or_404(Medico, usuario=request.user)
    estado_filtro = request.GET.get('estado')

    citas = Cita.objects.select_related(
        'paciente__usuario', 'horario', 'estado'
    ).filter(medico=medico)

    if estado_filtro:
        citas = citas.filter(estado__nombre=estado_filtro)

    citas = citas.order_by('-horario__fecha', '-horario__hora_inicio')
    estados = EstadoCita.objects.all()

    return render(request, 'medicos/citas_agendadas.html', {
        'citas': citas,
        'estados': estados,
        'estado_filtro': estado_filtro,
    })


@login_required
@require_http_methods(["POST"])
def marcar_realizada(request, pk):
    return _cambiar_estado_cita(request, pk, 'realizada', _('Cita marcada como realizada.'))


@login_required
@require_http_methods(["POST"])
def marcar_no_asistio(request, pk):
    return _cambiar_estado_cita(request, pk, 'no_asistio', _('Paciente marcado como no asistió.'))


def _cambiar_estado_cita(request, pk, nuevo_estado_nombre, msg_success):
    if request.user.rol != 'medico':
        messages.error(request, _('Solo los médicos pueden modificar citas.'))
        return redirect('dashboard')

    cita = get_object_or_404(
        Cita.objects.select_related('medico__usuario', 'horario', 'estado'),
        pk=pk, medico__usuario=request.user,
    )

    if cita.estado.nombre not in ('pendiente', 'confirmada'):
        messages.error(request, _('Solo se pueden modificar citas pendientes o confirmadas.'))
        return redirect('medicos:citas_agendadas')

    with transaction.atomic():
        nuevo_estado = EstadoCita.objects.get(nombre=nuevo_estado_nombre)
        cita.estado = nuevo_estado
        cita.save(update_fields=['estado'])

    messages.success(request, msg_success)
    return redirect('medicos:citas_agendadas')
