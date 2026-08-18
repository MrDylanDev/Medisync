from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import AuditoriaCita, Cita


class CitaSerializer(serializers.ModelSerializer):
    """
    Serializer for Cita (appointment) model.

    Includes read-only estado_nombre for convenience.
    Validates that the horario is available when creating.
    """

    estado_nombre = serializers.CharField(
        source="estado.nombre",
        read_only=True,
    )

    class Meta:
        model = Cita
        fields = [
            "id",
            "paciente",
            "medico",
            "horario",
            "estado",
            "estado_nombre",
            "motivo",
            "notas",
            "cancelada_por",
            "fecha_cancelacion",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "estado",  # solo cambia por los endpoints dedicados (cancelar, marcar realizada/no_asistió)
            "cancelada_por",
            "fecha_cancelacion",
            "created_at",
            "updated_at",
        ]

    def validate_horario(self, value):
        """Ensure the horario is available for booking."""
        if not value.disponible:
            raise serializers.ValidationError(_("El horario seleccionado no está disponible."))
        return value

    def validate(self, attrs):
        """Ensure the medico matches the horario's medico."""
        horario = attrs.get("horario")
        # En updates el medico no llega en attrs (es read-only en la vista);
        # se valida contra el medico ya asignado a la cita.
        medico = attrs.get("medico") or getattr(self.instance, "medico", None)
        if horario and medico and medico != horario.medico:
            raise serializers.ValidationError(
                {"medico": _("El médico no corresponde al horario seleccionado.")}
            )
        return attrs


class AuditoriaCitaSerializer(serializers.ModelSerializer):
    """Serializer for AuditoriaCita (audit trail entries)."""

    class Meta:
        model = AuditoriaCita
        fields = "__all__"
        read_only_fields = ["fecha_cambio"]
