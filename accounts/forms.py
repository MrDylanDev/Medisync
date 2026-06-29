from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

from core.utils import is_login_locked, register_failed_attempt, reset_login_attempts


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label=_('Correo electrónico'),
        widget=forms.EmailInput(attrs={
            'class': 'input',
            'placeholder': 'correo@ejemplo.com',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label=_('Contraseña'),
        widget=forms.PasswordInput(attrs={
            'class': 'input',
            'placeholder': 'Contraseña',
        }),
    )

    def clean(self):
        correo = self.cleaned_data.get('username')

        if correo and is_login_locked(correo):
            raise forms.ValidationError(
                _('Demasiados intentos fallidos. La cuenta está bloqueada por 15 minutos.'),
                code='account_locked',
            )

        try:
            user = super().clean()
        except forms.ValidationError:
            if correo:
                register_failed_attempt(correo)
            raise

        if correo:
            reset_login_attempts(correo)
        return user
