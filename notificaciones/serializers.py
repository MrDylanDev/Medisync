from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = [
            'id', 'usuario', 'tipo', 'titulo',
            'mensaje', 'leida', 'creado_en',
        ]
        read_only_fields = ['creado_en']


class NotificacionMarcarLeidaSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text=_('Lista de IDs de notificaciones a marcar como leídas'),
    )
