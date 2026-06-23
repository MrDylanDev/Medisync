from django.contrib import admin

from .models import Medico, MedicoEspecialidad, Horario


class MedicoEspecialidadInline(admin.TabularInline):
    model = MedicoEspecialidad
    extra = 1
    autocomplete_fields = ['especialidad']


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'precio_consulta', 'atencion_online', 'calificacion']
    list_filter = ['atencion_online']
    search_fields = ['usuario__correo', 'usuario__nombre', 'usuario__apellido', 'informacion_consultorio']
    ordering = ['usuario__apellido', 'usuario__nombre']
    autocomplete_fields = ['usuario']
    inlines = [MedicoEspecialidadInline]


@admin.register(MedicoEspecialidad)
class MedicoEspecialidadAdmin(admin.ModelAdmin):
    list_display = ['medico', 'especialidad', 'es_principal']
    list_filter = ['es_principal']
    search_fields = ['medico__usuario__nombre', 'medico__usuario__apellido', 'especialidad__nombre']
    autocomplete_fields = ['medico', 'especialidad']


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ['medico', 'fecha', 'hora_inicio', 'hora_fin', 'disponible']
    list_filter = ['disponible', 'fecha']
    search_fields = ['medico__usuario__nombre', 'medico__usuario__apellido']
    ordering = ['-fecha', 'medico']
    autocomplete_fields = ['medico']
    date_hierarchy = 'fecha'
