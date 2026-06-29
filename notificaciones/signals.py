import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from citas.models import Cita
from .models import Notificacion


def _fmt_fecha(fecha):
    if isinstance(fecha, datetime.date):
        return fecha.strftime('%d/%m/%Y')
    return str(fecha)


def _fmt_hora(hora):
    if isinstance(hora, datetime.time):
        return hora.strftime('%H:%M')
    return str(hora)


@receiver(post_save, sender=Cita)
def crear_notificacion_cita(sender, instance, created, **kwargs):
    if created:
        Notificacion.objects.create(
            usuario=instance.paciente.usuario,
            tipo='cita_confirmada',
            titulo='Cita confirmada',
            mensaje=(
                f'Tu cita con Dr. {instance.medico.usuario.nombre_completo} '
                f'para el {_fmt_fecha(instance.horario.fecha)} a las '
                f'{_fmt_hora(instance.horario.hora_inicio)} fue confirmada.'
            ),
        )

    if instance.estado.nombre == 'cancelada':
        if Notificacion.objects.filter(
            tipo='cita_cancelada',
            usuario=instance.paciente.usuario,
            creado_en__date=instance.updated_at.date(),
        ).exists():
            return

        Notificacion.objects.create(
            usuario=instance.paciente.usuario,
            tipo='cita_cancelada',
            titulo='Cita cancelada',
            mensaje=(
                f'Tu cita con Dr. {instance.medico.usuario.nombre_completo} '
                f'del {_fmt_fecha(instance.horario.fecha)} fue cancelada.'
            ),
        )
        Notificacion.objects.create(
            usuario=instance.medico.usuario,
            tipo='cita_cancelada',
            titulo='Cita cancelada',
            mensaje=(
                f'La cita con {instance.paciente.usuario.nombre_completo} '
                f'del {_fmt_fecha(instance.horario.fecha)} fue cancelada.'
            ),
        )
