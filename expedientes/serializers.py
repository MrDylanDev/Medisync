from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Expediente


class ExpedienteSerializer(serializers.ModelSerializer):
    paciente_nombre = serializers.SerializerMethodField()
    medico_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Expediente
        fields = [
            'id', 'paciente', 'medico', 'cita',
            'diagnostico', 'tratamiento', 'notas',
            'paciente_nombre', 'medico_nombre',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_paciente_nombre(self, obj):
        return obj.paciente.usuario.nombre_completo

    def get_medico_nombre(self, obj):
        return f'Dr. {obj.medico.usuario.nombre_completo}'
