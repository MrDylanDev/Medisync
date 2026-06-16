"""
Pytest configuration and shared fixtures for the Medisync project.

Sets the test database to SQLite to avoid requiring a running MySQL server.
"""
import os
os.environ.setdefault('DB_ENGINE', 'django.db.backends.sqlite3')
os.environ.setdefault('DB_NAME', ':memory:')

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Provide an unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Provide an authenticated API client."""
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def test_user(db):
    """Create a test user for authentication tests."""
    from accounts.models import Usuario
    user = Usuario.objects.create_user(
        correo='test@example.com',
        password='TestPass123!',
        nombre='Test',
        apellido='User',
        rol='paciente',
    )
    return user


@pytest.fixture
def test_medico_user(db):
    """Create a test doctor user."""
    from accounts.models import Usuario
    user = Usuario.objects.create_user(
        correo='medico@example.com',
        password='TestPass123!',
        nombre='Dr.',
        apellido='Medico',
        rol='medico',
    )
    return user


@pytest.fixture
def test_admin_user(db):
    """Create a test admin user."""
    from accounts.models import Usuario
    user = Usuario.objects.create_superuser(
        correo='admin@example.com',
        password='AdminPass123!',
        nombre='Admin',
        apellido='User',
    )
    return user
