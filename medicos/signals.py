from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Horario


@receiver(pre_save, sender=Horario)
def validar_horario_sin_superposicion(sender, instance, **kwargs):
    """
    Validate that the Horario does not overlap with existing slots
    for the same Medico on the same date.

    Overlap occurs when:
    - New start < existing end AND new end > existing start

    Adjacent slots (e.g., 9:00-10:00 and 10:00-11:00) are allowed.
    """
    if not instance.medico_id or not instance.fecha:
        return

    overlapping = Horario.objects.filter(
        medico=instance.medico,
        fecha=instance.fecha,
        hora_inicio__lt=instance.hora_fin,
        hora_fin__gt=instance.hora_inicio,
    )

    # Exclude self when updating
    if instance.pk:
        overlapping = overlapping.exclude(pk=instance.pk)

    if overlapping.exists():
        raise ValidationError(
            _('El horario se superpone con un turno existente para este médico '
              'en la fecha %(fecha)s.') % {'fecha': instance.fecha},
        )
