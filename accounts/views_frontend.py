from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import password_validation
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from core.utils import send_template_email
from .models import Usuario


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        rol = request.POST.get('rol', 'paciente')

        errors = {}

        if not correo:
            errors['correo'] = _('El correo es obligatorio.')
        elif Usuario.objects.filter(correo=correo).exists():
            errors['correo'] = _('Este correo ya está registrado.')

        if not nombre:
            errors['nombre'] = _('El nombre es obligatorio.')

        if not apellido:
            errors['apellido'] = _('El apellido es obligatorio.')

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

        if errors:
            return render(request, 'accounts/register.html', {
                'errors': errors,
                'form_data': {
                    'correo': correo,
                    'nombre': nombre,
                    'apellido': apellido,
                    'telefono': telefono,
                    'rol': rol,
                },
            })

        usuario = Usuario.objects.create_user(
            correo=correo,
            password=password,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            rol=rol,
        )
        usuario.save()

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
    return render(request, 'dashboard/dashboard.html')


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
