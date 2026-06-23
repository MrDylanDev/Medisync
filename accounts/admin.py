from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Usuario, Role, Paciente, Medico, TokenRecuperacion


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin):
    """Admin configuration for custom Usuario model."""
    fieldsets = (
        (None, {'fields': ('correo', 'password')}),
        (_('Información personal'), {'fields': ('nombre', 'apellido', 'telefono', 'rol')}),
        (
            _('Permisos'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_('Fechas importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('correo', 'nombre', 'apellido', 'rol', 'password1', 'password2'),
            },
        ),
    )
    list_display = ['correo', 'nombre', 'apellido', 'rol', 'is_active', 'is_staff']
    list_filter = ['rol', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['correo', 'nombre', 'apellido']
    ordering = ['apellido', 'nombre']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']
    ordering = ['nombre']


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'numero_historia_clinica', 'fecha_nacimiento', 'obra_social']
    list_filter = ['obra_social']
    search_fields = ['usuario__correo', 'usuario__nombre', 'usuario__apellido', 'numero_historia_clinica']
    ordering = ['usuario__apellido', 'usuario__nombre']
    autocomplete_fields = ['usuario']


@admin.register(Medico)
class MedicoProfileAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'numero_matricula', 'telefono_consultorio']
    search_fields = ['usuario__correo', 'usuario__nombre', 'usuario__apellido', 'numero_matricula']
    ordering = ['usuario__apellido', 'usuario__nombre']
    autocomplete_fields = ['usuario']


@admin.register(TokenRecuperacion)
class TokenRecuperacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'utilizado', 'creado_en', 'expira_en']
    list_filter = ['utilizado']
    search_fields = ['usuario__correo', 'token']
    ordering = ['-creado_en']
    readonly_fields = ['creado_en']
