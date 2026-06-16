from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CitasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'citas'
    verbose_name = _('Citas')

    def ready(self):
        import citas.signals  # noqa: F401
