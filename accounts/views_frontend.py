from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import password_validation
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from citas.models import Cita
from core.utils import send_template_email
from especialidades.models import Especialidad

from .models import Usuario, Medico as MedicoProfile
from .forms import EmailAuthenticationForm
from medicos.models import Medico as MedicoPractice


from django.views.decorators.http import require_http_methods, require_POST


@require_http_methods(["GET", "POST"])
def login_modal(request):
    if request.method == 'GET':
        return redirect('home')
    from django.contrib.auth.views import LoginView
    return LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=EmailAuthenticationForm,
        redirect_authenticated_user=True,
    )(request)


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        documento = request.POST.get('documento', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        rol = request.POST.get('rol', 'paciente')
        numero_matricula = request.POST.get('numero_matricula', '').strip()
        informacion_consultorio = request.POST.get('informacion_consultorio', '').strip()
        precio_consulta = request.POST.get('precio_consulta', '').strip()
        atencion_online = request.POST.get('atencion_online') == '1'

        errors = {}

        if not correo:
            errors['correo'] = _('El correo es obligatorio.')
        elif Usuario.objects.filter(correo=correo).exists():
            errors['correo'] = _('Este correo ya está registrado.')

        if not nombre:
            errors['nombre'] = _('El nombre es obligatorio.')

        if not apellido:
            errors['apellido'] = _('El apellido es obligatorio.')

        if documento and Usuario.objects.filter(documento=documento).exists():
            errors['documento'] = _('Este documento ya está registrado.')

        if not password:
            errors['password'] = _('La contraseña es obligatoria.')
        else:
            try:
                password_validation.validate_password(password)
            except ValidationError as e:
                errors['password'] = ' '.join(e.messages)

        if password != password_confirm:
            errors['password_confirm'] = _('Las contraseñas no coinciden.')

        if rol not in ('paciente', 'medico'):
            errors['rol'] = _('Rol inválido.')

        if rol == 'medico':
            if not numero_matricula:
                errors['numero_matricula'] = _('El número de matrícula es obligatorio para médicos.')
            elif MedicoProfile.objects.filter(numero_matricula=numero_matricula).exists():
                errors['numero_matricula'] = _('Esta matrícula ya está registrada.')

        if errors:
            return render(request, 'accounts/register.html', {
                'errors': errors,
                'form_data': {
                    'correo': correo,
                    'nombre': nombre,
                    'apellido': apellido,
                    'telefono': telefono,
                    'documento': documento,
                    'rol': rol,
                    'numero_matricula': numero_matricula,
                    'informacion_consultorio': informacion_consultorio,
                    'precio_consulta': precio_consulta,
                    'atencion_online': atencion_online,
                },
            })

        usuario = Usuario.objects.create_user(
            correo=correo,
            password=password,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            documento=documento or None,
            rol=rol,
        )

        if rol == 'medico':
            MedicoProfile.objects.create(
                usuario=usuario,
                numero_matricula=numero_matricula,
            )
            MedicoPractice.objects.create(
                usuario=usuario,
                informacion_consultorio=informacion_consultorio,
                precio_consulta=precio_consulta or 0,
                atencion_online=atencion_online,
            )

        auth_login(request, usuario)

        send_template_email(
            subject=f'¡Bienvenido a Medisync, {nombre}!',
            template_name='emails/registration_confirm.html',
            context={
                'nombre': nombre,
                'correo': correo,
                'rol': usuario.get_rol_display(),
            },
            recipient_list=[correo],
        )

        messages.success(request, _('¡Registro exitoso! Bienvenido a Medisync.'))
        return redirect('dashboard')

    return render(request, 'accounts/register.html')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {
        'usuario': request.user,
    })


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    ctx = {}
    u = request.user

    if u.rol == 'paciente':
        paciente = getattr(u, 'paciente', None)
        if paciente:
            ctx['total_citas'] = paciente.citas.count()
            ctx['pendientes'] = paciente.citas.filter(estado__nombre__in=['pendiente', 'confirmada']).count()
            ctx['realizadas'] = paciente.citas.filter(estado__nombre='realizada').count()
            ctx['citas_recientes'] = paciente.citas.select_related('medico__usuario', 'horario', 'estado').order_by('-horario__fecha', '-horario__hora_inicio')[:5]

    elif u.rol == 'medico':
        medico = getattr(u, 'medico', None)
        if medico:
            from django.utils import timezone
            today = timezone.localdate()
            ctx['citas_hoy'] = medico.citas.filter(horario__fecha=today).count()
            ctx['proximas'] = medico.citas.filter(horario__fecha__gt=today, estado__nombre__in=['pendiente', 'confirmada']).count()
            ctx['pacientes_atendidos'] = medico.citas.filter(estado__nombre='realizada').values('paciente').distinct().count()
            ctx['citas_recientes'] = medico.citas.select_related('paciente__usuario', 'horario', 'estado').order_by('-horario__fecha', '-horario__hora_inicio')[:5]

    elif u.rol == 'admin':
        ctx['total_usuarios'] = Usuario.objects.count()
        ctx['total_medicos'] = Usuario.objects.filter(rol='medico').count()
        ctx['total_especialidades'] = Especialidad.objects.count()
        from citas.models import Cita
        ctx['total_citas'] = Cita.objects.count()
        ctx['citas_recientes'] = Cita.objects.select_related('paciente__usuario', 'medico__usuario', 'horario', 'estado').order_by('-horario__fecha', '-horario__hora_inicio')[:5]

    return render(request, 'dashboard/dashboard.html', ctx)


# ─── Admin user management ────────────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_usuarios(request):
    search = request.GET.get('search', '')
    rol = request.GET.get('rol', '')
    activo = request.GET.get('activo', '')

    usuarios = Usuario.objects.all()
    if search:
        usuarios = usuarios.filter(
            Q(correo__icontains=search)
            | Q(nombre__icontains=search)
            | Q(apellido__icontains=search)
        )
    if rol:
        usuarios = usuarios.filter(rol=rol)
    if activo == 'true':
        usuarios = usuarios.filter(is_active=True)
    elif activo == 'false':
        usuarios = usuarios.filter(is_active=False)

    usuarios = usuarios.order_by('apellido', 'nombre')

    return render(request, 'admin/usuarios.html', {
        'usuarios': usuarios,
        'search': search,
        'rol_filtro': rol,
        'activo_filtro': activo,
    })


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def admin_bloquear_usuario_frontend(request, pk):
    user = get_object_or_404(Usuario, pk=pk)
    user.is_active = False
    user.save(update_fields=['is_active'])
    messages.success(request, _(f'Usuario {user.nombre_completo} bloqueado.'))
    return redirect('admin-usuarios')


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def admin_activar_usuario_frontend(request, pk):
    user = get_object_or_404(Usuario, pk=pk)
    user.is_active = True
    user.save(update_fields=['is_active'])
    messages.success(request, _(f'Usuario {user.nombre_completo} activado.'))
    return redirect('admin-usuarios')


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def admin_eliminar_usuario_frontend(request, pk):
    user = get_object_or_404(Usuario, pk=pk)
    if user.is_staff:
        messages.error(request, _('No se puede eliminar un administrador.'))
        return redirect('admin-usuarios')
    user.delete()
    messages.success(request, _('Usuario eliminado.'))
    return redirect('admin-usuarios')
