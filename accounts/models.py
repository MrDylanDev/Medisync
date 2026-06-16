from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator

from core.models import BaseModel
from .managers import UsuarioManager


class Usuario(AbstractUser):
    """
    Custom user model using email as the unique identifier.
    
    Replaces the default username field with correo (email) for
    authentication. All auth flows use email + password.
    """
    username = None
    correo = models.EmailField(
        _('correo electrónico'),
        unique=True,
        max_length=255,
        help_text=_('Dirección de correo electrónico del usuario'),
    )
    nombre = models.CharField(
        _('nombre'),
        max_length=100,
        help_text=_('Nombre del usuario'),
    )
    apellido = models.CharField(
        _('apellido'),
        max_length=100,
        help_text=_('Apellido del usuario'),
    )
    telefono = models.CharField(
        _('teléfono'),
        max_length=20,
        blank=True,
        help_text=_('Número de teléfono de contacto'),
    )
    rol = models.CharField(
        _('rol'),
        max_length=20,
        choices=[
            ('admin', 'Administrador'),
            ('medico', 'Médico'),
            ('paciente', 'Paciente'),
        ],
        default='paciente',
        help_text=_('Rol del usuario en el sistema'),
    )
    is_active = models.BooleanField(
        _('activo'),
        default=True,
        help_text=_('Indica si el usuario está activo'),
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    class Meta:
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f'{self.apellido}, {self.nombre} ({self.correo})'

    @property
    def nombre_completo(self):
        """Return the user's full name."""
        return f'{self.nombre} {self.apellido}'


class Role(models.Model):
    """
    Role model for system-wide permission management.
    
    Defines named roles with descriptions that can be assigned
    to groups of users for fine-grained access control.
    """
    nombre = models.CharField(
        _('nombre'),
        max_length=50,
        unique=True,
        help_text=_('Nombre del rol (ej: administrador, recepcionista)'),
    )
    descripcion = models.TextField(
        _('descripción'),
        blank=True,
        help_text=_('Descripción del rol y sus responsabilidades'),
    )

    class Meta:
        verbose_name = _('rol')
        verbose_name_plural = _('roles')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Paciente(BaseModel):
    """
    Patient profile model extending Usuario with medical record info.
    
    Each patient has one-to-one relationship with a Usuario account.
    Stores medical record number, date of birth, insurance details,
    and emergency contact information.
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='paciente',
        verbose_name=_('usuario'),
    )
    numero_historia_clinica = models.CharField(
        _('número de historia clínica'),
        max_length=20,
        unique=True,
        blank=True,
        help_text=_('Número único de historia clínica'),
    )
    fecha_nacimiento = models.DateField(
        _('fecha de nacimiento'),
        null=True,
        blank=True,
    )
    direccion = models.TextField(
        _('dirección'),
        blank=True,
        help_text=_('Dirección del paciente'),
    )
    obra_social = models.CharField(
        _('obra social'),
        max_length=100,
        blank=True,
        help_text=_('Obra social o prepaga del paciente'),
    )
    numero_afiliado = models.CharField(
        _('número de afiliado'),
        max_length=50,
        blank=True,
        help_text=_('Número de afiliado a la obra social'),
    )
    contacto_emergencia_nombre = models.CharField(
        _('nombre contacto emergencia'),
        max_length=200,
        blank=True,
    )
    contacto_emergencia_telefono = models.CharField(
        _('teléfono contacto emergencia'),
        max_length=20,
        blank=True,
    )

    class Meta:
        verbose_name = _('paciente')
        verbose_name_plural = _('pacientes')
        ordering = ['usuario__apellido', 'usuario__nombre']

    def __str__(self):
        return f'{self.usuario.nombre_completo} — HC: {self.numero_historia_clinica or "S/H"}'


class Medico(BaseModel):
    """
    Doctor profile model linking a Usuario to medical practice info.
    
    Stores professional contact details. Clinical specialty
    information is managed in the medicos app (MedicoEspecialidad).
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='medico_profile',
        verbose_name=_('usuario'),
    )
    numero_matricula = models.CharField(
        _('número de matrícula'),
        max_length=20,
        unique=True,
        help_text=_('Número de matrícula profesional'),
    )
    bio = models.TextField(
        _('biografía'),
        blank=True,
        help_text=_('Resumen profesional del médico'),
    )
    telefono_consultorio = models.CharField(
        _('teléfono consultorio'),
        max_length=20,
        blank=True,
    )

    class Meta:
        verbose_name = _('médico')
        verbose_name_plural = _('médicos')
        ordering = ['usuario__apellido', 'usuario__nombre']

    def __str__(self):
        return f'Dr. {self.usuario.nombre_completo} — Mat: {self.numero_matricula}'


class TokenRecuperacion(models.Model):
    """
    Password reset token model.
    
    Stores one-time use tokens for password recovery flows.
    Tokens expire after a configurable duration (default: 24 hours).
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_recuperacion',
        verbose_name=_('usuario'),
    )
    token = models.CharField(
        _('token'),
        max_length=255,
        unique=True,
        help_text=_('Token de recuperación'),
    )
    creado_en = models.DateTimeField(
        _('creado en'),
        auto_now_add=True,
    )
    utilizado = models.BooleanField(
        _('utilizado'),
        default=False,
        help_text=_('Indica si el token ya fue utilizado'),
    )
    expira_en = models.DateTimeField(
        _('expira en'),
        help_text=_('Fecha y hora de expiración del token'),
    )

    class Meta:
        verbose_name = _('token de recuperación')
        verbose_name_plural = _('tokens de recuperación')
        ordering = ['-creado_en']

    def __str__(self):
        return f'Token para {self.usuario.correo} — {"Usado" if self.utilizado else "Vigente"}'
