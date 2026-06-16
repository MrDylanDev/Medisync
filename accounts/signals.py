from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Paciente, Medico


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Signal handler that auto-creates a profile (Paciente or Medico)
    when a new Usuario is created, based on their assigned role.
    
    - 'paciente' role → creates a Paciente profile
    - 'medico' role → creates a Medico profile (basic stub without matricula)
    - 'admin' role → no profile needed
    """
    if not created:
        return

    if instance.rol == 'paciente':
        Paciente.objects.get_or_create(usuario=instance)
    elif instance.rol == 'medico':
        Medico.objects.get_or_create(
            usuario=instance,
            defaults={'numero_matricula': f'TEMP-{instance.id}'},
        )
