from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MedicosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicos'
    verbose_name = _('Médicos')

    def ready(self):
        import medicos.signals  # noqa: F401
