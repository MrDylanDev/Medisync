from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import Expediente


@login_required
def lista(request):
    if request.user.rol == 'paciente':
        expedientes = Expediente.objects.select_related(
            'medico__usuario', 'cita'
        ).filter(paciente__usuario=request.user).order_by('-created_at')
    elif request.user.rol == 'medico':
        expedientes = Expediente.objects.select_related(
            'paciente__usuario', 'cita'
        ).filter(medico__usuario=request.user).order_by('-created_at')
    else:
        expedientes = Expediente.objects.select_related(
            'paciente__usuario', 'medico__usuario', 'cita'
        ).all().order_by('-created_at')

    return render(request, 'expedientes/list.html', {
        'expedientes': expedientes,
    })


@login_required
@require_http_methods(["GET", "POST"])
def crear(request):
    if request.user.rol not in ('medico', 'admin'):
        messages.error(request, _('Solo los médicos pueden crear expedientes.'))
        return redirect('dashboard')

    from citas.models import Cita
    from accounts.models import Paciente

    pacientes = Paciente.objects.select_related('usuario').all().order_by('usuario__apellido')
    citas = Cita.objects.select_related('paciente__usuario', 'horario').filter(
        medico__usuario=request.user
    ) if request.user.rol == 'medico' else Cita.objects.select_related('paciente__usuario', 'horario').all()

    if request.method == 'POST':
        paciente_id = request.POST.get('paciente')
        cita_id = request.POST.get('cita')
        diagnostico = request.POST.get('diagnostico', '').strip()
        tratamiento = request.POST.get('tratamiento', '').strip()
        notas = request.POST.get('notas', '').strip()

        errors = {}
        if not paciente_id:
            errors['paciente'] = _('Debe seleccionar un paciente.')
        if not diagnostico:
            errors['diagnostico'] = _('El diagnóstico es obligatorio.')

        if errors:
            return render(request, 'expedientes/form.html', {
                'pacientes': pacientes,
                'citas': citas,
                'errors': errors,
                'form_data': request.POST,
            })

        from medicos.models import Medico
        medico = get_object_or_404(Medico, usuario=request.user) if request.user.rol == 'medico' else None

        expediente = Expediente.objects.create(
            paciente_id=paciente_id,
            medico=medico or Medico.objects.get(pk=request.POST.get('medico')),
            cita_id=cita_id or None,
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            notas=notas,
            created_by=request.user,
        )

        messages.success(request, _('Expediente creado correctamente.'))
        return redirect('expedientes:lista')

    return render(request, 'expedientes/form.html', {
        'pacientes': pacientes,
        'citas': citas,
        'medico_mode': request.user.rol == 'medico',
    })
