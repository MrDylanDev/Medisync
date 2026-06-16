from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Usuario, Paciente, Medico


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Validates password confirmation and creates a new Usuario
    with the provided credentials. Password confirmation field
    is write-only and removed after validation.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = Usuario
        fields = [
            'correo', 'nombre', 'apellido', 'telefono',
            'password', 'password_confirm', 'rol',
        ]

    def validate_correo(self, value):
        """Normalize and check email uniqueness."""
        return Usuario.objects.normalize_email(value)

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError(
                {'password_confirm': _('Las contraseñas no coinciden.')}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    Validates credentials (correo + password) and returns
    the authenticated Usuario instance on success.
    """
    correo = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        correo = attrs.get('correo')
        password = attrs.get('password')

        if correo and password:
            user = authenticate(
                request=self.context.get('request'),
                username=correo,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    _('Credenciales inválidas.'),
                    code='authentication_failed',
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    _('La cuenta está desactivada.'),
                    code='account_disabled',
                )
            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                _('Debe proporcionar correo y contraseña.'),
                code='missing_fields',
            )

        return attrs


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer for reading/updating Usuario profile.
    
    Excludes sensitive fields like password. Used for
    displaying user profile information.
    """
    class Meta:
        model = Usuario
        fields = [
            'id', 'correo', 'nombre', 'apellido',
            'telefono', 'rol', 'is_active',
        ]
        read_only_fields = ['id', 'is_active']


class PacienteSerializer(serializers.ModelSerializer):
    """Serializer for patient profile data."""
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Paciente
        fields = '__all__'
        read_only_fields = ['numero_historia_clinica']


class MedicoSerializer(serializers.ModelSerializer):
    """Serializer for doctor profile data."""
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Medico
        fields = '__all__'


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset.
    
    Takes an email address and sends a reset link
    if the email exists in the system (no error
    disclosure for security).
    """
    correo = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset.
    
    Validates the token and sets the new password.
    Requires token, new password, and confirmation.
    """
    token = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': _('Las contraseñas no coinciden.')}
            )
        return attrs
