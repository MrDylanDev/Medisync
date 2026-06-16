from django.conf import settings
from datetime import datetime


def global_template_vars(request):
    """
    Context processor providing global template variables.
    
    Makes app name, current year, and debug status available
    to all templates without per-view boilerplate.
    """
    return {
        'app_name': 'Medisync',
        'current_year': datetime.now().year,
        'debug': settings.DEBUG,
    }
