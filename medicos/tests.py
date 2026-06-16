"""
Tests for medicos app: models, signals, serializers, views.
"""
import pytest
from datetime import time, date, timedelta
from django.db import IntegrityError
from django.core.exceptions import ValidationError


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def medico_usuario(db):
    """Create a usuario with medico role."""
    from accounts.models import Usuario
    user = Usuario.objects.create_user(
        correo='medico@test.com',
        password='TestPass123!',
        nombre='Dr.',
        apellido='Test',
        rol='medico',
    )
    return user


@pytest.fixture
def especialidad(db):
    """Create a test especialidad."""
    from especialidades.models import Especialidad
    return Especialidad.objects.create(nombre='Cardiología')


@pytest.fixture
def medico(db, medico_usuario):
    """Create a Medico domain model instance."""
    from medicos.models import Medico
    return Medico.objects.create(
        usuario=medico_usuario,
        informacion_consultorio='Consultorio 3B, Edificio Central',
        precio_consulta=15000.00,
    )


# ─── Model: Medico ────────────────────────────────────────────────────────────

class TestMedicoModel:
    """Tests for Medico model."""

    def test_create_medico(self, db, medico_usuario):
        """Creating a valid Medico should succeed."""
        from medicos.models import Medico
        med = Medico.objects.create(
            usuario=medico_usuario,
            informacion_consultorio='Consultorio 101',
            precio_consulta=20000.00,
        )
        assert med.usuario == medico_usuario
        assert med.informacion_consultorio == 'Consultorio 101'
        assert med.precio_consulta == 20000.00
        assert med.atencion_online is False
        assert str(med) is not None

    def test_medico_one_to_one_usuario(self, db, medico_usuario):
        """One Medico per usuario."""
        from medicos.models import Medico
        Medico.objects.create(usuario=medico_usuario)
        with pytest.raises(IntegrityError):
            Medico.objects.create(usuario=medico_usuario)

    def test_medico_default_online_off(self, db, medico_usuario):
        """atencion_online should default to False."""
        from medicos.models import Medico
        med = Medico.objects.create(usuario=medico_usuario)
        assert med.atencion_online is False

    def test_medico_calificacion_default(self, db, medico_usuario):
        """calificacion should default to 0.0."""
        from medicos.models import Medico
        med = Medico.objects.create(usuario=medico_usuario)
        assert med.calificacion == 0.0


# ─── Model: MedicoEspecialidad ────────────────────────────────────────────────

class TestMedicoEspecialidadModel:
    """Tests for MedicoEspecialidad model."""

    def test_create_medico_especialidad(self, db, medico, especialidad):
        """Creating a valid MedicoEspecialidad should succeed."""
        from medicos.models import MedicoEspecialidad
        me = MedicoEspecialidad.objects.create(
            medico=medico,
            especialidad=especialidad,
        )
        assert me.medico == medico
        assert me.especialidad == especialidad
        assert me.es_principal is False

    def test_unique_medico_especialidad(self, db, medico, especialidad):
        """Duplicate medico+especialidad should raise."""
        from medicos.models import MedicoEspecialidad
        MedicoEspecialidad.objects.create(medico=medico, especialidad=especialidad)
        with pytest.raises(IntegrityError):
            MedicoEspecialidad.objects.create(medico=medico, especialidad=especialidad)


# ─── Model: Horario ──────────────────────────────────────────────────────────

class TestHorarioModel:
    """Tests for Horario model."""

    def test_create_horario(self, db, medico):
        """Creating a valid Horario should succeed."""
        from medicos.models import Horario
        h = Horario.objects.create(
            medico=medico,
            fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
        )
        assert h.medico == medico
        assert h.fecha == date(2026, 6, 17)
        assert h.hora_inicio == time(9, 0)
        assert h.hora_fin == time(10, 0)
        assert h.disponible is True

    def test_horario_disponible_default(self, db, medico):
        """Horario should be disponible by default."""
        from medicos.models import Horario
        h = Horario.objects.create(
            medico=medico,
            fecha=date(2026, 6, 17),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
        )
        assert h.disponible is True

    def test_horario_unique_constraint(self, db, medico):
        """Same medico+fecha+hora_inicio+hora_fin should raise (signal catches first)."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico,
            fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
        )
        with pytest.raises((IntegrityError, ValidationError)):
            Horario.objects.create(
                medico=medico,
                fecha=date(2026, 6, 17),
                hora_inicio=time(9, 0),
                hora_fin=time(10, 0),
            )

    def test_horario_different_fecha_ok(self, db, medico):
        """Same times on different dates should be allowed."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico,
            fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
        )
        # Same times, different date - should succeed
        h2 = Horario.objects.create(
            medico=medico,
            fecha=date(2026, 6, 18),
            hora_inicio=time(9, 0),
            hora_fin=time(10, 0),
        )
        assert h2.id is not None

    def test_horario_hora_fin_greater_than_hora_inicio(self, db, medico):
        """hora_fin must be > hora_inicio. Check constraint at DB level."""
        from medicos.models import Horario
        with pytest.raises(IntegrityError):
            Horario.objects.create(
                medico=medico,
                fecha=date(2026, 6, 17),
                hora_inicio=time(10, 0),
                hora_fin=time(9, 0),
            )

    def test_horario_equal_times(self, db, medico):
        """hora_fin == hora_inicio should raise IntegrityError."""
        from medicos.models import Horario
        with pytest.raises(IntegrityError):
            Horario.objects.create(
                medico=medico,
                fecha=date(2026, 6, 17),
                hora_inicio=time(10, 0),
                hora_fin=time(10, 0),
            )


# ─── Signals: Horario Overlap Validation ─────────────────────────────────────

class TestHorarioOverlapSignal:
    """Tests for Horario overlap validation signal."""

    def test_overlapping_start_inside_existing(self, db, medico):
        """New slot starting within existing slot should be rejected."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        with pytest.raises(ValidationError, match='superpone'):
            Horario.objects.create(
                medico=medico, fecha=date(2026, 6, 17),
                hora_inicio=time(9, 30), hora_fin=time(10, 30),
            )

    def test_overlapping_end_inside_existing(self, db, medico):
        """New slot ending within existing slot should be rejected."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        with pytest.raises(ValidationError, match='superpone'):
            Horario.objects.create(
                medico=medico, fecha=date(2026, 6, 17),
                hora_inicio=time(8, 30), hora_fin=time(9, 30),
            )

    def test_overlapping_fully_contained(self, db, medico):
        """New slot fully inside existing slot should be rejected."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0), hora_fin=time(11, 0),
        )
        with pytest.raises(ValidationError, match='superpone'):
            Horario.objects.create(
                medico=medico, fecha=date(2026, 6, 17),
                hora_inicio=time(9, 30), hora_fin=time(10, 0),
            )

    def test_overlapping_encompasses_existing(self, db, medico):
        """New slot fully containing existing slot should be rejected."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 30), hora_fin=time(10, 0),
        )
        with pytest.raises(ValidationError, match='superpone'):
            Horario.objects.create(
                medico=medico, fecha=date(2026, 6, 17),
                hora_inicio=time(9, 0), hora_fin=time(11, 0),
            )

    def test_adjacent_slot_before_ok(self, db, medico):
        """New slot ending exactly at existing slot start should be OK."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(10, 0), hora_fin=time(11, 0),
        )
        h = Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        assert h.id is not None

    def test_adjacent_slot_after_ok(self, db, medico):
        """New slot starting exactly at existing slot end should be OK."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        h = Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 17),
            hora_inicio=time(10, 0), hora_fin=time(11, 0),
        )
        assert h.id is not None

    def test_different_medico_no_overlap(self, db, medico_usuario):
        """Same times but different medico should be OK."""
        from medicos.models import Medico, Horario
        medico1 = Medico.objects.create(usuario=medico_usuario)
        from accounts.models import Usuario
        otro_user = Usuario.objects.create_user(
            correo='otro@test.com', password='TestPass123!',
            nombre='Otro', apellido='Doc', rol='medico',
        )
        medico2 = Medico.objects.create(usuario=otro_user)

        Horario.objects.create(
            medico=medico1, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        h = Horario.objects.create(
            medico=medico2, fecha=date(2026, 6, 17),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        assert h.id is not None


# ─── Fixtures for API tests ─────────────────────────────────────────────────

@pytest.fixture
def admin_client(db, test_admin_user):
    """Provide an authenticated admin API client."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=test_admin_user)
    return client


# ─── API: Serializers ───────────────────────────────────────────────────────

class TestMedicoSerializer:
    """Tests for MedicoSerializer."""

    def test_serialize_medico(self, db, medico):
        """Serializer should return correct fields."""
        from medicos.serializers import MedicoSerializer
        serializer = MedicoSerializer(medico)
        assert 'id' in serializer.data
        assert 'usuario' in serializer.data
        assert 'informacion_consultorio' in serializer.data

    def test_deserialize_valid(self, db, medico_usuario):
        """Valid data should deserialize."""
        from medicos.serializers import MedicoSerializer
        data = {
            'usuario': medico_usuario.id,
            'informacion_consultorio': 'Consultorio 5',
            'precio_consulta': '25000.00',
        }
        serializer = MedicoSerializer(data=data)
        assert serializer.is_valid(), f'Errors: {serializer.errors}'


class TestHorarioSerializer:
    """Tests for HorarioSerializer."""

    def test_serialize_horario(self, db, medico):
        """Serializer should return correct fields."""
        from medicos.models import Horario
        from medicos.serializers import HorarioSerializer
        h = Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 20),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        serializer = HorarioSerializer(h)
        assert 'id' in serializer.data
        assert serializer.data['disponible'] is True


# ─── API: Views — Medico CRUD ──────────────────────────────────────────────

class TestMedicoListEndpoint:
    """Tests for GET /api/medicos/."""

    LIST_URL = '/api/medicos/'

    def test_list_authenticated(self, authenticated_client, db, medico):
        """Authenticated user should list medicos."""
        response = authenticated_client.get(self.LIST_URL, format='json')
        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_list_unauthenticated(self, api_client, db):
        """Unauthenticated user should get 401."""
        response = api_client.get(self.LIST_URL, format='json')
        assert response.status_code == 401


class TestMedicoCreateEndpoint:
    """Tests for POST /api/medicos/."""

    LIST_URL = '/api/medicos/'

    def test_create_as_admin(self, admin_client, db, test_admin_user):
        """Admin should create medico."""
        from accounts.models import Usuario
        doc_user = Usuario.objects.create_user(
            correo='nuevo@test.com', password='TestPass123!',
            nombre='Nuevo', apellido='Doc', rol='medico',
        )
        data = {
            'usuario': doc_user.id,
            'informacion_consultorio': 'Consultorio 10',
            'precio_consulta': '30000.00',
        }
        response = admin_client.post(self.LIST_URL, data, format='json')
        assert response.status_code == 201

    def test_create_as_regular_user(self, authenticated_client, db, medico_usuario):
        """Regular user should NOT create medico."""
        data = {
            'usuario': medico_usuario.id,
            'precio_consulta': '10000.00',
        }
        response = authenticated_client.post(self.LIST_URL, data, format='json')
        assert response.status_code == 403


class TestMedicoDetailEndpoint:
    """Tests for GET/PUT/DELETE /api/medicos/{id}/."""

    def test_detail(self, authenticated_client, db, medico):
        """Authenticated user should view a medico."""
        response = authenticated_client.get(f'/api/medicos/{medico.id}/', format='json')
        assert response.status_code == 200
        assert 'informacion_consultorio' in response.data

    def test_update_as_admin(self, admin_client, db, medico):
        """Admin should update medico."""
        response = admin_client.patch(
            f'/api/medicos/{medico.id}/',
            {'precio_consulta': '50000.00'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['precio_consulta'] == '50000.00'

    def test_delete_as_admin(self, admin_client, db, medico):
        """Admin should delete medico."""
        response = admin_client.delete(f'/api/medicos/{medico.id}/', format='json')
        assert response.status_code == 204


# ─── API: Disponibilidad (available slots) ─────────────────────────────────

class TestDisponibilidadEndpoint:
    """Tests for GET /api/medicos/{id}/disponibilidad/."""

    def test_disponibilidad_by_date(self, authenticated_client, db, medico):
        """Search slots by date should return matching horarios."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 20),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 20),
            hora_inicio=time(10, 0), hora_fin=time(11, 0),
        )
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 21),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        response = authenticated_client.get(
            f'/api/medicos/{medico.id}/disponibilidad/?fecha=2026-06-20',
            format='json',
        )
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_disponibilidad_no_results(self, authenticated_client, db, medico):
        """Date with no slots should return empty list."""
        response = authenticated_client.get(
            f'/api/medicos/{medico.id}/disponibilidad/?fecha=2026-07-01',
            format='json',
        )
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_disponibilidad_missing_date(self, authenticated_client, db, medico):
        """Missing fecha param should return 400."""
        response = authenticated_client.get(
            f'/api/medicos/{medico.id}/disponibilidad/',
            format='json',
        )
        assert response.status_code == 400

    def test_disponibilidad_medico_not_found(self, authenticated_client, db):
        """Non-existent medico should return 404."""
        response = authenticated_client.get(
            '/api/medicos/999/disponibilidad/?fecha=2026-06-20',
            format='json',
        )
        assert response.status_code == 404

    def test_disponibilidad_only_available(self, authenticated_client, db, medico):
        """Only disponible=True slots should be returned."""
        from medicos.models import Horario
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 20),
            hora_inicio=time(9, 0), hora_fin=time(10, 0),
        )
        Horario.objects.create(
            medico=medico, fecha=date(2026, 6, 20),
            hora_inicio=time(10, 0), hora_fin=time(11, 0),
            disponible=False,
        )
        response = authenticated_client.get(
            f'/api/medicos/{medico.id}/disponibilidad/?fecha=2026-06-20',
            format='json',
        )
        assert response.status_code == 200
        assert len(response.data) == 1
