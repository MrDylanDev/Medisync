from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from medicos.models import Medico

from .models import Expediente


@login_required
def lista(request):
    if request.user.rol == "paciente":
        expedientes = (
            Expediente.objects.select_related("medico__usuario", "cita")
            .filter(paciente__usuario=request.user)
            .order_by("-created_at")
        )
    elif request.user.rol == "medico":
        expedientes = (
            Expediente.objects.select_related("paciente__usuario", "cita")
            .filter(medico__usuario=request.user)
            .order_by("-created_at")
        )
    else:
        expedientes = (
            Expediente.objects.select_related("paciente__usuario", "medico__usuario", "cita")
            .all()
            .order_by("-created_at")
        )

    return render(
        request,
        "expedientes/list.html",
        {
            "expedientes": expedientes,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def crear(request):
    if request.user.rol not in ("medico", "admin"):
        messages.error(request, _("Solo los médicos pueden crear expedientes."))
        return redirect("dashboard")

    from accounts.models import Paciente
    from citas.models import Cita

    pacientes = Paciente.objects.select_related("usuario").all().order_by("usuario__apellido")
    citas = (
        Cita.objects.select_related("paciente__usuario", "horario").filter(
            medico__usuario=request.user
        )
        if request.user.rol == "medico"
        else Cita.objects.select_related("paciente__usuario", "horario").all()
    )

    if request.method == "POST":
        paciente_id = request.POST.get("paciente")
        cita_id = request.POST.get("cita")
        diagnostico = request.POST.get("diagnostico", "").strip()
        tratamiento = request.POST.get("tratamiento", "").strip()
        notas = request.POST.get("notas", "").strip()

        errors = {}
        if not paciente_id:
            errors["paciente"] = _("Debe seleccionar un paciente.")
        if not diagnostico:
            errors["diagnostico"] = _("El diagnóstico es obligatorio.")

        # Validate medico field for admin role
        medico_instance = None
        if request.user.rol == "admin":
            medico_id = request.POST.get("medico")
            if not medico_id:
                errors["medico"] = _("Debe seleccionar un médico.")
            else:
                try:
                    medico_instance = Medico.objects.get(pk=medico_id)
                except (Medico.DoesNotExist, ValueError):
                    errors["medico"] = _("Médico inválido.")
        else:
            medico_instance = get_object_or_404(Medico, usuario=request.user)

        # Validate cita belongs to the selected paciente
        if cita_id and paciente_id:
            from citas.models import Cita

            try:
                cita_obj = Cita.objects.get(pk=cita_id)
                if str(cita_obj.paciente_id) != str(paciente_id):
                    errors["cita"] = _(
                        "La cita seleccionada no pertenece al paciente elegido."
                    )
            except (Cita.DoesNotExist, ValueError):
                errors["cita"] = _("Cita inválida.")

        if errors:
            return render(
                request,
                "expedientes/form.html",
                {
                    "pacientes": pacientes,
                    "citas": citas,
                    "medicos": Medico.objects.select_related("usuario").all()
                    if request.user.rol == "admin"
                    else [],
                    "errors": errors,
                    "form_data": request.POST,
                },
            )

        Expediente.objects.create(
            paciente_id=paciente_id,
            medico=medico_instance,
            cita_id=cita_id or None,
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            notas=notas,
            created_by=request.user,
        )

        messages.success(request, _("Expediente creado correctamente."))
        return redirect("expedientes:lista")

    medicos_list = (
        Medico.objects.select_related("usuario").all()
        if request.user.rol == "admin"
        else []
    )

    return render(
        request,
        "expedientes/form.html",
        {
            "pacientes": pacientes,
            "citas": citas,
            "medicos": medicos_list,
            "medico_mode": request.user.rol == "medico",
        },
    )
