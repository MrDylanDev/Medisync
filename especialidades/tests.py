"""
Tests for especialidades app: models, admin, serializers, views.
"""
import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient


@pytest.fixture
def admin_client(db, test_admin_user):
    """Provide an authenticated admin API client."""
    client = APIClient()
    client.force_authenticate(user=test_admin_user)
    return client


# ─── Model: Especialidad ─────────────────────────────────────────────────────

class TestEspecialidadModel:
    """Tests for Especialidad model."""

    def test_create_especialidad(self, db):
        """Creating a valid Especialidad should succeed."""
        from especialidades.models import Especialidad
        esp = Especialidad.objects.create(
            nombre='Cardiología',
            descripcion='Especialidad del corazón y sistema circulatorio',
        )
        assert esp.nombre == 'Cardiología'
        assert esp.descripcion == 'Especialidad del corazón y sistema circulatorio'
        assert esp.activo is True
        assert str(esp) == 'Cardiología'

    def test_especialidad_default_activo(self, db):
        """New Especialidad should be active by default."""
        from especialidades.models import Especialidad
        esp = Especialidad.objects.create(nombre='Pediatría')
        assert esp.activo is True

    def test_especialidad_unique_nombre(self, db):
        """Duplicate nombre should raise IntegrityError."""
        from especialidades.models import Especialidad
        Especialidad.objects.create(nombre='Dermatología')
        with pytest.raises(IntegrityError):
            Especialidad.objects.create(nombre='Dermatología')

    def test_especialidad_ordering(self, db):
        """Especialidades should be ordered by nombre."""
        from especialidades.models import Especialidad
        Especialidad.objects.create(nombre='Zología')
        Especialidad.objects.create(nombre='Anatomía')
        Especialidad.objects.create(nombre='Biología')
        esp_list = list(Especialidad.objects.all())
        assert esp_list[0].nombre == 'Anatomía'
        assert esp_list[1].nombre == 'Biología'
        assert esp_list[2].nombre == 'Zología'

    def test_especialidad_inactive_filter(self, db):
        """Should be able to filter by activo status."""
        from especialidades.models import Especialidad
        Especialidad.objects.create(nombre='Activa', activo=True)
        Especialidad.objects.create(nombre='Inactiva', activo=False)
        assert Especialidad.objects.filter(activo=True).count() == 1
        assert Especialidad.objects.filter(activo=False).count() == 1


# ─── Admin ────────────────────────────────────────────────────────────────────

class TestEspecialidadAdmin:
    """Tests for Especialidad admin configuration."""

    def test_especialidad_registered(self, db):
        """Especialidad should be registered in admin."""
        from django.contrib import admin
        from especialidades.models import Especialidad
        assert admin.site.is_registered(Especialidad)

    def test_admin_list_display(self):
        """Admin should have correct list_display fields."""
        from especialidades.admin import EspecialidadAdmin
        assert 'nombre' in EspecialidadAdmin.list_display
        assert 'activo' in EspecialidadAdmin.list_display

    def test_admin_search_fields(self):
        """Admin should have search_fields for nombre."""
        from especialidades.admin import EspecialidadAdmin
        assert 'nombre' in EspecialidadAdmin.search_fields


# ─── API: Serializers ────────────────────────────────────────────────────────

class TestEspecialidadSerializer:
    """Tests for EspecialidadSerializer."""

    def test_serialize_especialidad(self, db):
        """Serializer should return correct fields."""
        from especialidades.models import Especialidad
        esp = Especialidad.objects.create(nombre='Neurología')
        from especialidades.serializers import EspecialidadSerializer
        serializer = EspecialidadSerializer(esp)
        assert serializer.data['nombre'] == 'Neurología'
        assert 'id' in serializer.data
        assert 'activo' in serializer.data

    def test_deserialize_valid(self, db):
        """Valid data should deserialize correctly."""
        from especialidades.serializers import EspecialidadSerializer
        serializer = EspecialidadSerializer(data={
            'nombre': 'Traumatología',
            'descripcion': 'Huesos y articulaciones',
        })
        assert serializer.is_valid(), f'Errors: {serializer.errors}'

    def test_deserialize_missing_nombre(self, db):
        """Missing nombre should fail validation."""
        from especialidades.serializers import EspecialidadSerializer
        serializer = EspecialidadSerializer(data={'descripcion': 'Sin nombre'})
        assert serializer.is_valid() is False
        assert 'nombre' in serializer.errors


# ─── API: Views ──────────────────────────────────────────────────────────────

class TestEspecialidadListEndpoint:
    """Tests for GET /api/especialidades/."""

    LIST_URL = '/api/especialidades/'

    def test_list_authenticated(self, authenticated_client, db):
        """Authenticated user should be able to list especialidades."""
        from especialidades.models import Especialidad
        Especialidad.objects.create(nombre='Cardiología')
        Especialidad.objects.create(nombre='Pediatría')
        response = authenticated_client.get(self.LIST_URL, format='json')
        assert response.status_code == 200
        assert len(response.data['results']) == 2

    def test_list_unauthenticated(self, api_client, db):
        """Unauthenticated user should get 401."""
        response = api_client.get(self.LIST_URL, format='json')
        assert response.status_code == 401

    def test_list_pagination(self, authenticated_client, db):
        """List should be paginated."""
        from especialidades.models import Especialidad
        for i in range(25):
            Especialidad.objects.create(nombre=f'Especialidad {i}')
        response = authenticated_client.get(self.LIST_URL, format='json')
        assert 'count' in response.data
        assert 'results' in response.data


class TestEspecialidadCreateEndpoint:
    """Tests for POST /api/especialidades/."""

    LIST_URL = '/api/especialidades/'

    def test_create_as_admin(self, admin_client, db):
        """Admin user should be able to create especialidad."""
        data = {'nombre': 'Oftalmología', 'descripcion': 'Ojos y visión'}
        response = admin_client.post(self.LIST_URL, data, format='json')
        assert response.status_code == 201
        assert response.data['nombre'] == 'Oftalmología'

    def test_create_as_regular_user(self, authenticated_client, db):
        """Regular user should NOT be able to create especialidad."""
        data = {'nombre': 'Oftalmología'}
        response = authenticated_client.post(self.LIST_URL, data, format='json')
        assert response.status_code == 403


class TestEspecialidadDetailEndpoint:
    """Tests for GET/PUT/DELETE /api/especialidades/{id}/."""

    def test_detail_authenticated(self, authenticated_client, db):
        """Authenticated user should view a single especialidad."""
        from especialidades.models import Especialidad
        esp = Especialidad.objects.create(nombre='Dermatología')
        response = authenticated_client.get(f'/api/especialidades/{esp.id}/', format='json')
        assert response.status_code == 200
        assert response.data['nombre'] == 'Dermatología'

    def test_detail_not_found(self, authenticated_client, db):
        """Non-existent id should return 404."""
        response = authenticated_client.get('/api/especialidades/999/', format='json')
        assert response.status_code == 404

    def test_update_as_admin(self, admin_client, db):
        """Admin should update especialidad."""
        from especialidades.models import Especialidad
        esp = Especialidad.objects.create(nombre='Viejo Nombre')
        response = admin_client.put(
            f'/api/especialidades/{esp.id}/',
            {'nombre': 'Nuevo Nombre', 'descripcion': ''},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['nombre'] == 'Nuevo Nombre'

    def test_delete_as_admin(self, admin_client, db):
        """Admin should delete especialidad."""
        from especialidades.models import Especialidad
        esp = Especialidad.objects.create(nombre='Eliminar')
        response = admin_client.delete(f'/api/especialidades/{esp.id}/', format='json')
        assert response.status_code == 204
        assert not Especialidad.objects.filter(id=esp.id).exists()

    def test_delete_as_regular_user(self, authenticated_client, db):
        """Regular user should NOT delete especialidad."""
        from especialidades.models import Especialidad
        esp = Especialidad.objects.create(nombre='Protegida')
        response = authenticated_client.delete(f'/api/especialidades/{esp.id}/', format='json')
        assert response.status_code == 403
