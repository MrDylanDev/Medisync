from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'tipo', 'titulo', 'leida', 'creado_en')
    list_filter = ('tipo', 'leida', 'creado_en')
    search_fields = ('usuario__correo', 'titulo')
