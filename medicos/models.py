from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from core.models import BaseModel


class Medico(BaseModel):
    """
    Doctor domain model with practice information.

    Extends the user profile with practice-specific fields like
    consultory info, pricing, online attention availability, and
    average rating from patient reviews.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medico_datos_created',
        verbose_name=_('creado por'),
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medico_datos',
        verbose_name=_('usuario'),
    )
    informacion_consultorio = models.TextField(
        _('información del consultorio'),
        blank=True,
        help_text=_('Dirección y datos del consultorio'),
    )
    precio_consulta = models.DecimalField(
        _('precio consulta'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Precio de la consulta médica'),
    )
    atencion_online = models.BooleanField(
        _('atención online'),
        default=False,
        help_text=_('Indica si ofrece atención virtual'),
    )
    calificacion = models.DecimalField(
        _('calificación'),
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text=_('Calificación promedio del médico'),
    )

    class Meta:
        verbose_name = _('médico')
        verbose_name_plural = _('médicos')
        ordering = ['usuario__apellido', 'usuario__nombre']

    def __str__(self):
        return f'Dr. {self.usuario.nombre_completo}'


class MedicoEspecialidad(models.Model):
    """
    Junction model linking Medico to Especialidad.

    Allows a doctor to have multiple specialties with one marked
    as primary (es_principal). Each combination is unique.
    """
    medico = models.ForeignKey(
        Medico,
        on_delete=models.CASCADE,
        related_name='especialidades',
        verbose_name=_('médico'),
    )
    especialidad = models.ForeignKey(
        'especialidades.Especialidad',
        on_delete=models.CASCADE,
        related_name='medicos',
        verbose_name=_('especialidad'),
    )
    es_principal = models.BooleanField(
        _('es principal'),
        default=False,
        help_text=_('Indica si esta es la especialidad principal del médico'),
    )

    class Meta:
        verbose_name = _('especialidad del médico')
        verbose_name_plural = _('especialidades de los médicos')
        unique_together = ['medico', 'especialidad']
        ordering = ['medico', 'especialidad']

    def __str__(self):
        return f'{self.medico} — {self.especialidad}'


class Horario(models.Model):
    """
    Doctor's available time slots.

    Each slot represents a block of time on a specific date where
    a doctor is available for appointments. The disponible flag is
    set to False when a Cita is booked for this slot.
    """
    medico = models.ForeignKey(
        Medico,
        on_delete=models.CASCADE,
        related_name='horarios',
        verbose_name=_('médico'),
    )
    fecha = models.DateField(
        _('fecha'),
        help_text=_('Fecha del horario disponible'),
    )
    hora_inicio = models.TimeField(
        _('hora inicio'),
        help_text=_('Hora de inicio del turno'),
    )
    hora_fin = models.TimeField(
        _('hora fin'),
        help_text=_('Hora de fin del turno'),
    )
    disponible = models.BooleanField(
        _('disponible'),
        default=True,
        help_text=_('Indica si el turno está disponible'),
    )

    class Meta:
        verbose_name = _('horario')
        verbose_name_plural = _('horarios')
        ordering = ['fecha', 'hora_inicio']
        constraints = [
            models.UniqueConstraint(
                fields=['medico', 'fecha', 'hora_inicio', 'hora_fin'],
                name='unique_medico_fecha_horario',
            ),
            models.CheckConstraint(
                condition=models.Q(hora_fin__gt=models.F('hora_inicio')),
                name='check_hora_fin_gt_hora_inicio',
            ),
        ]

    def __str__(self):
        return f'{self.medico} — {self.fecha} {self.hora_inicio}-{self.hora_fin}'
