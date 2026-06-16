from django.db import models
from django.utils.translation import gettext_lazy as _


class Especialidad(models.Model):
    """
    Medical specialty model.

    Stores medical specialties (e.g., Cardiology, Pediatrics) that can be
    assigned to doctors via MedicoEspecialidad. Specialties can be soft-deactivated
    via the activo flag rather than being deleted.
    """
    nombre = models.CharField(
        _('nombre'),
        max_length=100,
        unique=True,
        help_text=_('Nombre de la especialidad médica'),
    )
    descripcion = models.TextField(
        _('descripción'),
        blank=True,
        help_text=_('Descripción detallada de la especialidad'),
    )
    activo = models.BooleanField(
        _('activo'),
        default=True,
        help_text=_('Indica si la especialidad está activa'),
    )

    class Meta:
        verbose_name = _('especialidad')
        verbose_name_plural = _('especialidades')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
