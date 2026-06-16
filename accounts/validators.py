import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UppercaseAndSpecialValidator:
    """
    Password validator requiring at least one uppercase letter,
    one digit, and one special character.
    
    Used in AUTH_PASSWORD_VALIDATORS to enforce password complexity
    beyond Django's built-in validators.
    """

    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos una mayúscula.'),
                code='password_no_upper',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos un dígito.'),
                code='password_no_digit',
            )
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError(
                _('La contraseña debe contener al menos un carácter especial.'),
                code='password_no_special',
            )

    def get_help_text(self):
        return _(
            'La contraseña debe contener al menos una mayúscula, '
            'un dígito y un carácter especial.'
        )
