from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
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
        elif len(password) < 8:
            errors['password'] = _('La contraseña debe tener al menos 8 caracteres.')

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
