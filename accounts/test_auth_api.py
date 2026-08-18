"""
Integration tests for the auth API endpoints.
"""

from django.contrib.auth import get_user_model
from rest_framework import status

Usuario = get_user_model()


class TestRegisterEndpoint:
    """Tests for POST /api/auth/register/."""

    REGISTER_URL = "/api/auth/register/"

    def test_register_success(self, api_client, db):
        """Registering with valid data should return 201 and JWT tokens."""
        data = {
            "correo": "newuser@test.com",
            "nombre": "New",
            "apellido": "User",
            "password": "StrongPass1!",
            "password_confirm": "StrongPass1!",
            "rol": "paciente",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["correo"] == "newuser@test.com"
        # Verify user was created in DB
        assert Usuario.objects.filter(correo="newuser@test.com").exists()

    def test_register_password_mismatch(self, api_client, db):
        """Registering with mismatched passwords should return 400."""
        data = {
            "correo": "mismatch@test.com",
            "nombre": "Mismatch",
            "apellido": "User",
            "password": "StrongPass1!",
            "password_confirm": "DifferentPass1!",
            "rol": "paciente",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data

    def test_register_duplicate_email(self, api_client, db, test_user):
        """Registering with existing email should return 400."""
        data = {
            "correo": "test@example.com",
            "nombre": "Duplicate",
            "apellido": "User",
            "password": "StrongPass1!",
            "password_confirm": "StrongPass1!",
            "rol": "paciente",
        }
        response = api_client.post(self.REGISTER_URL, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self, api_client, db):
        """Registering without required fields should return 400."""
        response = api_client.post(self.REGISTER_URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLoginEndpoint:
    """Tests for POST /api/auth/login/."""

    LOGIN_URL = "/api/auth/login/"

    def test_login_success(self, api_client, db, test_user):
        """Logging in with valid credentials should return 200 and JWT."""
        data = {
            "correo": "test@example.com",
            "password": "TestPass123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["correo"] == "test@example.com"

    def test_login_invalid_password(self, api_client, db, test_user):
        """Logging in with wrong password should return 401."""
        data = {
            "correo": "test@example.com",
            "password": "WrongPass123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, api_client, db):
        """Logging in with unregistered email should return 401."""
        data = {
            "correo": "nobody@test.com",
            "password": "TestPass123!",
        }
        response = api_client.post(self.LOGIN_URL, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProfileEndpoint:
    """Tests for GET/PUT/PATCH /api/auth/profile/."""

    PROFILE_URL = "/api/auth/profile/"

    def test_get_profile_authenticated(self, authenticated_client, db):
        """Authenticated user should be able to view their profile."""
        response = authenticated_client.get(self.PROFILE_URL, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["correo"] == "test@example.com"

    def test_get_profile_unauthenticated(self, api_client, db):
        """Unauthenticated user should get 401."""
        response = api_client.get(self.PROFILE_URL, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, authenticated_client, db):
        """Authenticated user should be able to update their profile."""
        data = {"nombre": "UpdatedName", "telefono": "123456789"}
        response = authenticated_client.patch(self.PROFILE_URL, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["nombre"] == "UpdatedName"
        assert response.data["telefono"] == "123456789"


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout/."""

    LOGOUT_URL = "/api/auth/logout/"

    def test_logout_without_refresh_token(self, authenticated_client, db):
        """Logout without refresh token should return 400."""
        response = authenticated_client.post(self.LOGOUT_URL, {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_unauthenticated(self, api_client, db):
        """Unauthenticated user should get 401."""
        response = api_client.post(self.LOGOUT_URL, {}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordResetEndpoint:
    """Tests for password reset endpoints."""

    RESET_URL = "/api/auth/password-reset/"
    RESET_CONFIRM_URL = "/api/auth/password-reset/confirm/"

    def test_reset_request_valid_email(self, api_client, db, test_user):
        """Reset request should create a token and send an email."""
        from django.core import mail
        from django.utils import timezone

        from accounts.models import TokenRecuperacion

        response = api_client.post(self.RESET_URL, {"correo": "test@example.com"}, format="json")
        assert response.status_code == status.HTTP_200_OK

        token = TokenRecuperacion.objects.get(usuario=test_user, utilizado=False)
        assert token.expira_en > timezone.now()
        assert len(mail.outbox) == 1
        assert "test@example.com" in mail.outbox[0].to
        assert token.token in mail.outbox[0].body

    def test_reset_request_unknown_email_no_enumeration(self, api_client, db):
        """Unknown email returns 200 (no user enumeration) and creates no token."""
        from accounts.models import TokenRecuperacion

        response = api_client.post(self.RESET_URL, {"correo": "nobody@test.com"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert not TokenRecuperacion.objects.exists()

    def test_reset_request_invalid_email(self, api_client, db):
        """Password reset request with invalid email should return 400."""
        data = {"correo": "not-an-email"}
        response = api_client.post(self.RESET_URL, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_confirm_valid(self, api_client, db, test_user):
        """Confirm with a valid one-time token should update the password."""
        from datetime import timedelta

        from django.utils import timezone

        from accounts.models import TokenRecuperacion

        recuperacion = TokenRecuperacion.objects.create(
            usuario=test_user,
            token="valid-token-123",
            expira_en=timezone.now() + timedelta(hours=1),
        )
        response = api_client.post(
            self.RESET_CONFIRM_URL,
            {
                "token": "valid-token-123",
                "password": "NewPass123!",
                "password_confirm": "NewPass123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        test_user.refresh_from_db()
        assert test_user.check_password("NewPass123!")
        recuperacion.refresh_from_db()
        assert recuperacion.utilizado is True

    def test_reset_confirm_invalid_token(self, api_client, db, test_user):
        """Confirm with an unknown token should return 400."""
        response = api_client.post(
            self.RESET_CONFIRM_URL,
            {
                "token": "does-not-exist",
                "password": "NewPass123!",
                "password_confirm": "NewPass123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        test_user.refresh_from_db()
        assert test_user.check_password("TestPass123!")

    def test_reset_confirm_expired_token(self, api_client, db, test_user):
        """Confirm with an expired token should return 400."""
        from datetime import timedelta

        from django.utils import timezone

        from accounts.models import TokenRecuperacion

        TokenRecuperacion.objects.create(
            usuario=test_user,
            token="expired-token",
            expira_en=timezone.now() - timedelta(hours=1),
        )
        response = api_client.post(
            self.RESET_CONFIRM_URL,
            {
                "token": "expired-token",
                "password": "NewPass123!",
                "password_confirm": "NewPass123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_confirm_used_token(self, api_client, db, test_user):
        """Confirm with an already-used token should return 400."""
        from datetime import timedelta

        from django.utils import timezone

        from accounts.models import TokenRecuperacion

        TokenRecuperacion.objects.create(
            usuario=test_user,
            token="used-token",
            expira_en=timezone.now() + timedelta(hours=1),
            utilizado=True,
        )
        response = api_client.post(
            self.RESET_CONFIRM_URL,
            {
                "token": "used-token",
                "password": "NewPass123!",
                "password_confirm": "NewPass123!",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_confirm_password_mismatch(self, api_client, db):
        """Password reset with mismatched passwords should return 400."""
        data = {
            "token": "valid-token",
            "password": "NewPass123!",
            "password_confirm": "DifferentPass1!",
        }
        response = api_client.post(self.RESET_CONFIRM_URL, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reset_confirm_weak_password(self, api_client, db, test_user):
        """Password reset with a weak password should return 400."""
        from datetime import timedelta

        from django.utils import timezone

        from accounts.models import TokenRecuperacion

        TokenRecuperacion.objects.create(
            usuario=test_user,
            token="weak-token",
            expira_en=timezone.now() + timedelta(hours=1),
        )
        response = api_client.post(
            self.RESET_CONFIRM_URL,
            {
                "token": "weak-token",
                "password": "weak",
                "password_confirm": "weak",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
