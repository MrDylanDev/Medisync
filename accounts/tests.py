"""
Tests for accounts app: models, managers, validators, serializers, views.
"""
import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from accounts.validators import UppercaseAndSpecialValidator
from accounts.models import Paciente, Medico, TokenRecuperacion
from accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UsuarioSerializer,
)

Usuario = get_user_model()


# ─── Managers ────────────────────────────────────────────────────────────────

class TestUsuarioManager:
    """Tests for UsuarioManager."""

    def test_create_user_success(self, db):
        """Creating a regular user should succeed."""
        user = Usuario.objects.create_user(
            correo='user@test.com',
            password='TestPass123!',
            nombre='John',
            apellido='Doe',
        )
        assert user.correo == 'user@test.com'
        assert user.nombre == 'John'
        assert user.apellido == 'Doe'
        assert user.check_password('TestPass123!') is True
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_without_email_raises(self, db):
        """Creating a user without email should raise ValueError."""
        with pytest.raises(ValueError, match='correo electrónico es obligatorio'):
            Usuario.objects.create_user(correo='', password='TestPass123!')

    def test_create_superuser_success(self, db):
        """Creating a superuser should grant staff and superuser status."""
        admin = Usuario.objects.create_superuser(
            correo='admin@test.com',
            password='AdminPass123!',
            nombre='Admin',
            apellido='User',
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.rol == 'admin'

    def test_create_user_normalizes_email(self, db):
        """Email should be normalized (lowercased domain)."""
        user = Usuario.objects.create_user(
            correo='User@Test.COM',
            password='TestPass123!',
            nombre='Test',
            apellido='User',
        )
        assert user.correo == 'User@test.com'

    def test_duplicate_email_raises(self, db):
        """Creating a user with an existing email should raise IntegrityError."""
        Usuario.objects.create_user(
            correo='dup@test.com',
            password='TestPass123!',
            nombre='First',
            apellido='User',
        )
        with pytest.raises(Exception):  # IntegrityError
            Usuario.objects.create_user(
                correo='dup@test.com',
                password='TestPass123!',
                nombre='Second',
                apellido='User',
            )


# ─── Models: Usuario ─────────────────────────────────────────────────────────

class TestUsuarioModel:
    """Tests for Usuario model."""

    def test_str_representation(self, db, test_user):
        """String representation should include name and email."""
        expected = f'{test_user.apellido}, {test_user.nombre} ({test_user.correo})'
        assert str(test_user) == expected

    def test_nombre_completo_property(self, db, test_user):
        """Nombre completo property should return full name."""
        assert test_user.nombre_completo == 'Test User'

    def test_username_field_is_correo(self):
        """USERNAME_FIELD should be 'correo'."""
        assert Usuario.USERNAME_FIELD == 'correo'

    def test_default_role_is_paciente(self, db):
        """Default role should be 'paciente'."""
        user = Usuario.objects.create_user(
            correo='default@test.com',
            password='TestPass123!',
            nombre='Default',
            apellido='User',
        )
        assert user.rol == 'paciente'


# ─── Models: Paciente ────────────────────────────────────────────────────────

class TestPacienteModel:
    """Tests for Paciente model."""

    def test_paciente_profile_created_by_signal(self, db, test_user):
        """Paciente profile should be auto-created by signal for paciente role."""
        assert hasattr(test_user, 'paciente')
        assert test_user.paciente is not None

    def test_paciente_str_representation(self, db, test_user):
        """String representation should include patient name."""
        paciente = test_user.paciente
        paciente.numero_historia_clinica = 'HC-001'
        paciente.save()
        assert 'Test User' in str(paciente)
        assert 'HC-001' in str(paciente)


# ─── Models: Medico ──────────────────────────────────────────────────────────

class TestMedicoModel:
    """Tests for Medico model."""

    def test_medico_profile_created_by_signal(self, db, test_medico_user):
        """Medico profile should be auto-created by signal for medico role."""
        assert hasattr(test_medico_user, 'medico_profile')
        assert test_medico_user.medico_profile is not None

    def test_medico_str_representation(self, db, test_medico_user):
        """String representation should include doctor name and license."""
        medico = test_medico_user.medico_profile
        medico.numero_matricula = 'MAT-12345'
        medico.save()
        assert 'Dr.' in str(medico)
        assert 'MAT-12345' in str(medico)

    def test_unique_matricula(self, db, test_medico_user):
        """Matricula number should be unique."""
        medico = test_medico_user.medico_profile
        medico.numero_matricula = 'MAT-UNIQUE'
        medico.save()
        otro_user = Usuario.objects.create_user(
            correo='otro@test.com',
            password='TestPass123!',
            nombre='Otro',
            apellido='Doc',
            rol='medico',
        )
        with pytest.raises(Exception):
            Medico.objects.create(
                usuario=otro_user,
                numero_matricula='MAT-UNIQUE',
            )


# ─── Models: TokenRecuperacion ───────────────────────────────────────────────

class TestTokenRecuperacion:
    """Tests for TokenRecuperacion model."""

    def test_create_token(self, db, test_user):
        """Creating a recovery token should work."""
        from datetime import datetime, timedelta
        token = TokenRecuperacion.objects.create(
            usuario=test_user,
            token='test-token-123',
            expira_en=datetime.now() + timedelta(hours=24),
        )
        assert token.usuario == test_user
        assert token.utilizado is False
        assert str(token) is not None


# ─── Validators ──────────────────────────────────────────────────────────────

class TestUppercaseAndSpecialValidator:
    """Tests for UppercaseAndSpecialValidator."""

    def setup_method(self):
        self.validator = UppercaseAndSpecialValidator()

    def test_valid_password(self):
        """Password with uppercase, digit, and special char should pass."""
        try:
            self.validator.validate('TestPass1!')
        except ValidationError:
            pytest.fail('Valid password raised ValidationError')

    def test_missing_uppercase_raises(self):
        """Password without uppercase should fail."""
        with pytest.raises(ValidationError, match='mayúscula'):
            self.validator.validate('testpass1!')

    def test_missing_digit_raises(self):
        """Password without digit should fail."""
        with pytest.raises(ValidationError, match='dígito'):
            self.validator.validate('TestPass!!')

    def test_missing_special_char_raises(self):
        """Password without special character should fail."""
        with pytest.raises(ValidationError, match='especial'):
            self.validator.validate('TestPass1')

    def test_help_text_includes_requirements(self):
        """Help text should mention all requirements."""
        help_text = self.validator.get_help_text()
        assert 'mayúscula' in help_text
        assert 'dígito' in help_text
        assert 'especial' in help_text


# ─── Serializers: Register ───────────────────────────────────────────────────

class TestRegisterSerializer:
    """Tests for RegisterSerializer."""

    def test_valid_registration_data(self, db):
        """Valid registration data should pass validation."""
        data = {
            'correo': 'newuser@test.com',
            'nombre': 'New',
            'apellido': 'User',
            'password': 'StrongPass1!',
            'password_confirm': 'StrongPass1!',
            'rol': 'paciente',
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), f'Errors: {serializer.errors}'

    def test_password_mismatch(self, db):
        """Mismatched passwords should fail validation."""
        data = {
            'correo': 'newuser@test.com',
            'nombre': 'New',
            'apellido': 'User',
            'password': 'StrongPass1!',
            'password_confirm': 'DifferentPass1!',
            'rol': 'paciente',
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid() is False
        assert 'password_confirm' in serializer.errors

    def test_missing_required_fields(self, db):
        """Missing required fields should fail validation."""
        serializer = RegisterSerializer(data={})
        assert serializer.is_valid() is False
        assert 'correo' in serializer.errors
        assert 'nombre' in serializer.errors
        assert 'password' in serializer.errors


# ─── Serializers: Login ──────────────────────────────────────────────────────

class TestLoginSerializer:
    """Tests for LoginSerializer."""

    def test_valid_credentials(self, db, test_user):
        """Valid credentials should pass validation."""
        from django.test.client import RequestFactory
        factory = RequestFactory()
        request = factory.post('/api/auth/login/')

        data = {
            'correo': 'test@example.com',
            'password': 'TestPass123!',
        }
        serializer = LoginSerializer(data=data, context={'request': request})
        assert serializer.is_valid(), f'Errors: {serializer.errors}'
        assert 'user' in serializer.validated_data

    def test_invalid_credentials(self, db):
        """Invalid credentials should fail validation."""
        from django.test.client import RequestFactory
        factory = RequestFactory()
        request = factory.post('/api/auth/login/')

        data = {
            'correo': 'test@example.com',
            'password': 'WrongPassword1!',
        }
        serializer = LoginSerializer(data=data, context={'request': request})
        assert serializer.is_valid() is False
        assert 'Credenciales inválidas' in str(serializer.errors)

    def test_missing_fields(self, db):
        """Missing email or password should fail."""
        serializer = LoginSerializer(data={})
        assert serializer.is_valid() is False


# ─── Serializers: Usuario ────────────────────────────────────────────────────

class TestUsuarioSerializer:
    """Tests for UsuarioSerializer."""

    def test_serialize_user(self, db, test_user):
        """Serializing a user should return correct fields."""
        serializer = UsuarioSerializer(test_user)
        data = serializer.data
        assert data['correo'] == 'test@example.com'
        assert data['nombre'] == 'Test'
        assert data['apellido'] == 'User'
        assert data['rol'] == 'paciente'
        assert 'password' not in data

    def test_update_user(self, db, test_user):
        """Updating a user via serializer should work."""
        serializer = UsuarioSerializer(
            test_user,
            data={'nombre': 'Updated', 'telefono': '123456789'},
            partial=True,
        )
        assert serializer.is_valid(), f'Errors: {serializer.errors}'
        serializer.save()
        test_user.refresh_from_db()
        assert test_user.nombre == 'Updated'
        assert test_user.telefono == '123456789'


# ─── Signal: crear_perfil_usuario ────────────────────────────────────────────

class TestCrearPerfilSignals:
    """Tests for auto-profile creation signal."""

    def test_create_user_creates_paciente_profile(self, db):
        """Creating a paciente user should auto-create Paciente profile."""
        user = Usuario.objects.create_user(
            correo='paciente@test.com',
            password='TestPass123!',
            nombre='Paciente',
            apellido='Test',
            rol='paciente',
        )
        assert hasattr(user, 'paciente')
        assert user.paciente is not None

    def test_create_user_creates_medico_profile(self, db):
        """Creating a medico user should auto-create Medico profile."""
        user = Usuario.objects.create_user(
            correo='medico@test.com',
            password='TestPass123!',
            nombre='Doctor',
            apellido='Test',
            rol='medico',
        )
        assert hasattr(user, 'medico_profile')
        assert user.medico_profile is not None

    def test_admin_user_has_no_profile(self, db):
        """Creating an admin user should NOT create a profile."""
        admin = Usuario.objects.create_superuser(
            correo='admin@test.com',
            password='AdminPass123!',
            nombre='Admin',
            apellido='Test',
        )
        assert not hasattr(admin, 'paciente')
        assert not hasattr(admin, 'medico_profile')
