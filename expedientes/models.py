from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Expediente(BaseModel):
    """
    Medical record entry for a patient.
    
    Each entry records a diagnosis, treatment, or clinical note
    made by a doctor during or after an appointment.
    """
    paciente = models.ForeignKey(
        'accounts.Paciente',
        on_delete=models.CASCADE,
        related_name='expedientes',
        verbose_name=_('paciente'),
    )
    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE,
        related_name='expedientes',
        verbose_name=_('médico'),
    )
    cita = models.ForeignKey(
        'citas.Cita',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expedientes',
        verbose_name=_('cita'),
    )
    diagnostico = models.TextField(
        _('diagnóstico'),
        help_text=_('Diagnóstico del paciente'),
    )
    tratamiento = models.TextField(
        _('tratamiento'),
        blank=True,
        help_text=_('Tratamiento recetado'),
    )
    notas = models.TextField(
        _('notas adicionales'),
        blank=True,
        help_text=_('Notas clínicas adicionales'),
    )

    class Meta:
        verbose_name = _('expediente')
        verbose_name_plural = _('expedientes')
        ordering = ['-created_at']

    def __str__(self):
        return f'Expediente #{self.id} — {self.paciente} — Dr. {self.medico}'
