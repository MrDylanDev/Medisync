from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notificacion(models.Model):
    """
    In-app notification for users.
    
    Tracks system-generated messages about appointments,
    reminders, and other important events.
    """
    TIPOS = [
        ('cita_confirmada', _('Cita confirmada')),
        ('cita_cancelada', _('Cita cancelada')),
        ('recordatorio', _('Recordatorio')),
        ('expediente_nuevo', _('Nuevo expediente')),
        ('sistema', _('Sistema')),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name=_('usuario'),
    )
    tipo = models.CharField(
        _('tipo'),
        max_length=30,
        choices=TIPOS,
        default='sistema',
    )
    titulo = models.CharField(
        _('título'),
        max_length=200,
    )
    mensaje = models.TextField(
        _('mensaje'),
    )
    leida = models.BooleanField(
        _('leída'),
        default=False,
    )
    creado_en = models.DateTimeField(
        _('creado en'),
        auto_now_add=True,
    )

    class Meta:
        verbose_name = _('notificación')
        verbose_name_plural = _('notificaciones')
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.usuario.correo} — {"Leída" if self.leida else "No leída"}'
