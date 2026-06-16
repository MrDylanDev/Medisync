from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Cita, AuditoriaCita
from accounts.serializers import UsuarioSerializer


class CitaSerializer(serializers.ModelSerializer):
    """
    Serializer for Cita (appointment) model.

    Includes read-only estado_nombre for convenience.
    Validates that the horario is available when creating.
    """
    estado_nombre = serializers.CharField(
        source='estado.nombre',
        read_only=True,
    )

    class Meta:
        model = Cita
        fields = [
            'id', 'paciente', 'medico', 'horario',
            'estado', 'estado_nombre', 'motivo', 'notas',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_horario(self, value):
        """Ensure the horario is available for booking."""
        if not value.disponible:
            raise serializers.ValidationError(
                _('El horario seleccionado no está disponible.')
            )
        return value


class AuditoriaCitaSerializer(serializers.ModelSerializer):
    """Serializer for AuditoriaCita (audit trail entries)."""

    class Meta:
        model = AuditoriaCita
        fields = '__all__'
        read_only_fields = ['fecha_cambio']
