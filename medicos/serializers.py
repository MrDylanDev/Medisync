from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import Medico, MedicoEspecialidad, Horario
from accounts.serializers import UsuarioSerializer


class MedicoSerializer(serializers.ModelSerializer):
    """
    Serializer for Medico domain model.

    Includes nested Usuario read-only info and supports
    full CRUD for admin users.
    """
    usuario_detail = UsuarioSerializer(source='usuario', read_only=True)

    class Meta:
        model = Medico
        fields = [
            'id', 'usuario', 'usuario_detail',
            'informacion_consultorio', 'precio_consulta',
            'atencion_online', 'calificacion',
        ]
        read_only_fields = ['calificacion']


class MedicoEspecialidadSerializer(serializers.ModelSerializer):
    """Serializer for MedicoEspecialidad junction model."""

    class Meta:
        model = MedicoEspecialidad
        fields = ['id', 'medico', 'especialidad', 'es_principal']


class HorarioSerializer(serializers.ModelSerializer):
    """Serializer for Horario (available time slots)."""

    class Meta:
        model = Horario
        fields = [
            'id', 'medico', 'fecha',
            'hora_inicio', 'hora_fin', 'disponible',
        ]
