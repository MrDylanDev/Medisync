from django.contrib import admin

from .models import Expediente


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'medico', 'cita', 'created_at')
    list_filter = ('medico', 'created_at')
    search_fields = ('paciente__usuario__nombre', 'paciente__usuario__apellido', 'diagnostico')
