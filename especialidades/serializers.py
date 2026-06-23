from rest_framework import serializers

from .models import Especialidad


class EspecialidadSerializer(serializers.ModelSerializer):
    """
    Serializer for Especialidad model.

    Provides full CRUD support for medical specialties.
    The activo field allows soft-deactivation instead of deletion.
    """

    class Meta:
        model = Especialidad
        fields = ['id', 'nombre', 'descripcion', 'activo']
