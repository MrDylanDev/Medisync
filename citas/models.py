from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class EstadoCita(models.Model):
    """
    Appointment status lookup table.

    Pre-populated with 5 states:
        1. pendiente — Waiting for confirmation
        2. confirmada — Confirmed by patient
        3. realizada — Completed (attended)
        4. cancelada — Cancelled
        5. no_asistio — Patient didn't show up
    """
    nombre = models.CharField(
        _('nombre'),
        max_length=50,
        unique=True,
        help_text=_('Nombre del estado (pendiente, confirmada, realizada, cancelada, no_asistio)'),
    )
    descripcion = models.TextField(
        _('descripción'),
        blank=True,
        help_text=_('Descripción del estado'),
    )

    class Meta:
        verbose_name = _('estado de cita')
        verbose_name_plural = _('estados de citas')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Cita(BaseModel):
    """
    Appointment model linking patient, doctor, and time slot.

    Each Cita is associated with a unique Horario to prevent
    double-booking. The estado field tracks the lifecycle of
    the appointment through its different states.
    """
    paciente = models.ForeignKey(
        'accounts.Paciente',
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name=_('paciente'),
    )
    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name=_('médico'),
    )
    horario = models.ForeignKey(
        'medicos.Horario',
        on_delete=models.CASCADE,
        related_name='citas',
        verbose_name=_('horario'),
        unique=True,
    )
    estado = models.ForeignKey(
        EstadoCita,
        on_delete=models.PROTECT,
        default=1,
        related_name='citas',
        verbose_name=_('estado'),
    )
    motivo = models.TextField(
        _('motivo'),
        help_text=_('Motivo de la consulta'),
    )
    notas = models.TextField(
        _('notas'),
        blank=True,
        help_text=_('Notas internas sobre la cita'),
    )
    cancelada_por = models.CharField(
        _('cancelada por'),
        max_length=10,
        blank=True,
        null=True,
        choices=[
            ('paciente', 'Paciente'),
            ('medico', 'Médico'),
            ('admin', 'Administrador'),
        ],
        help_text=_('Quién canceló la cita'),
    )
    fecha_cancelacion = models.DateTimeField(
        _('fecha de cancelación'),
        blank=True,
        null=True,
        help_text=_('Fecha y hora en que se canceló la cita'),
    )

    class Meta:
        verbose_name = _('cita')
        verbose_name_plural = _('citas')
        ordering = ['-created_at']

    def __str__(self):
        return f'Cita #{self.id} — {self.paciente} con {self.medico} — {self.estado.nombre}'


class AuditoriaCita(models.Model):
    """
    Audit trail for appointment state changes.

    Records every state transition of a Cita, including
    who made the change, what the old and new states were,
    and a free-text note explaining the reason.
    """
    cita = models.ForeignKey(
        Cita,
        on_delete=models.CASCADE,
        related_name='auditorias',
        verbose_name=_('cita'),
    )
    estado_anterior = models.ForeignKey(
        EstadoCita,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_('estado anterior'),
    )
    estado_nuevo = models.ForeignKey(
        EstadoCita,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name=_('estado nuevo'),
    )
    cambiado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias_citas',
        verbose_name=_('cambiado por'),
    )
    fecha_cambio = models.DateTimeField(
        _('fecha de cambio'),
        auto_now_add=True,
    )
    nota = models.TextField(
        _('nota'),
        blank=True,
        help_text=_('Nota explicativa del cambio'),
    )

    class Meta:
        verbose_name = _('auditoría de cita')
        verbose_name_plural = _('auditorías de citas')
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f'Auditoría #{self.id} — Cita #{self.cita_id} — {self.estado_nuevo.nombre}'
