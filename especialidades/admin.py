from django.contrib import admin

from .models import Especialidad


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    """Admin configuration for Especialidad model."""
    list_display = ['nombre', 'activo']
    search_fields = ['nombre']
    list_filter = ['activo']
    ordering = ['nombre']
