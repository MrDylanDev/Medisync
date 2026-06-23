from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import EstadoCita, Cita, AuditoriaCita


@admin.register(EstadoCita)
class EstadoCitaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


class AuditoriaCitaInline(admin.TabularInline):
    model = AuditoriaCita
    extra = 0
    readonly_fields = ['estado_anterior', 'estado_nuevo', 'cambiado_por', 'fecha_cambio', 'nota']
    can_delete = False
    max_num = 0


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['id', 'paciente', 'medico', 'fecha', 'hora', 'estado', 'created_at']
    list_filter = ['estado', 'created_at']
    search_fields = [
        'paciente__usuario__correo',
        'paciente__usuario__nombre',
        'paciente__usuario__apellido',
        'medico__usuario__nombre',
        'medico__usuario__apellido',
    ]
    ordering = ['-created_at']
    autocomplete_fields = ['paciente', 'medico', 'horario', 'estado']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [AuditoriaCitaInline]

    def fecha(self, obj):
        return obj.horario.fecha

    def hora(self, obj):
        return f'{obj.horario.hora_inicio} — {obj.horario.hora_fin}'

    fecha.short_description = _('fecha')
    fecha.admin_order_field = 'horario__fecha'
    hora.short_description = _('horario')


@admin.register(AuditoriaCita)
class AuditoriaCitaAdmin(admin.ModelAdmin):
    list_display = ['cita', 'estado_anterior', 'estado_nuevo', 'cambiado_por', 'fecha_cambio']
    list_filter = ['estado_nuevo', 'fecha_cambio']
    search_fields = ['cita__id', 'cambiado_por__correo']
    ordering = ['-fecha_cambio']
    readonly_fields = ['cita', 'estado_anterior', 'estado_nuevo', 'cambiado_por', 'fecha_cambio']
    date_hierarchy = 'fecha_cambio'
