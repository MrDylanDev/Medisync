from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Cita, AuditoriaCita


@receiver(pre_save, sender=Cita)
def capturar_estado_anterior(sender, instance, **kwargs):
    """
    Capture the previous estado before a Cita is saved.

    Stores the old estado on the instance itself so the post_save
    handler can compare and create an audit entry if it changed.
    """
    if instance.pk:
        try:
            instance._estado_anterior = Cita.objects.get(pk=instance.pk).estado
        except Cita.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Cita)
def crear_auditoria_cita(sender, instance, created, **kwargs):
    """
    Create an AuditoriaCita entry when a Cita is created or its estado changes.

    - On creation: logs the initial estado (estado_anterior=None)
    - On update: logs the transition if estado changed
    - No entry is created when non-estado fields change (e.g., notas)
    """
    old = getattr(instance, '_estado_anterior', None)
    if created or old != instance.estado:
        AuditoriaCita.objects.create(
            cita=instance,
            estado_anterior=old,
            estado_nuevo=instance.estado,
            cambiado_por=instance.created_by if instance.created_by_id else None,
            nota='',
        )
