"""
Tests for citas app: models, signals, serializers, views.
"""
import pytest
from datetime import time, date, timedelta
from django.db import IntegrityError


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def paciente_usuario(db):
    """Create a usuario with paciente role."""
    from accounts.models import Usuario
    user = Usuario.objects.create_user(
        correo='paciente@test.com',
        password='TestPass123!',
        nombre='Paciente',
        apellido='Test',
        rol='paciente',
    )
    return user


@pytest.fixture
def paciente(db, paciente_usuario):
    """Create a Paciente profile."""
    from accounts.models import Paciente
    return Paciente.objects.get(usuario=paciente_usuario)


@pytest.fixture
def medico_usuario(db):
    """Create a usuario with medico role."""
    from accounts.models import Usuario
    user = Usuario.objects.create_user(
        correo='doctor@test.com',
        password='TestPass123!',
        nombre='Dr.',
        apellido='Medico',
        rol='medico',
    )
    return user


@pytest.fixture
def medico(db, medico_usuario):
    """Create a Medico domain model instance."""
    from medicos.models import Medico
    return Medico.objects.create(usuario=medico_usuario)


@pytest.fixture
def horario(db, medico):
    """Create a Horario for the medico."""
    from medicos.models import Horario
    return Horario.objects.create(
        medico=medico,
        fecha=date(2026, 6, 20),
        hora_inicio=time(10, 0),
        hora_fin=time(11, 0),
    )


@pytest.fixture
def estado_pendiente(db):
    """Get the 'pendiente' EstadoCita (seeded by data migration)."""
    from citas.models import EstadoCita
    return EstadoCita.objects.get(nombre='pendiente')


@pytest.fixture
def cita(db, paciente, horario, estado_pendiente):
    """Create a sample Cita."""
    from citas.models import Cita
    return Cita.objects.create(
        paciente=paciente, medico=horario.medico,
        horario=horario, estado=estado_pendiente,
        motivo='Consulta de rutina',
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user for audit tracking (no profile auto-created)."""
    from accounts.models import Usuario
    return Usuario.objects.create_superuser(
        correo='admin@test.com',
        password='AdminPass123!',
        nombre='Admin',
        apellido='User',
    )


# ─── Model: EstadoCita ───────────────────────────────────────────────────────

class TestEstadoCitaModel:
    """Tests for EstadoCita model."""

    def test_estados_seeded(self, db):
        """Five estados should be seeded by data migration."""
        from citas.models import EstadoCita
        assert EstadoCita.objects.count() == 5

    def test_estado_str(self, db):
        """String representation should return nombre."""
        from citas.models import EstadoCita
        estado = EstadoCita.objects.get(nombre='pendiente')
        assert str(estado) == 'pendiente'

    def test_estado_unique_nombre(self, db):
        """Duplicate nombre should raise IntegrityError."""
        from citas.models import EstadoCita
        with pytest.raises(IntegrityError):
            EstadoCita.objects.create(nombre='pendiente')


# ─── Model: Cita ─────────────────────────────────────────────────────────────

class TestCitaModel:
    """Tests for Cita model."""

    def test_create_cita(self, db, paciente, horario, estado_pendiente):
        """Creating a valid Cita should succeed."""
        from citas.models import Cita
        cita = Cita.objects.create(
            paciente=paciente,
            medico=horario.medico,
            horario=horario,
            estado=estado_pendiente,
            motivo='Consulta general',
        )
        assert cita.paciente == paciente
        assert cita.medico == horario.medico
        assert cita.horario == horario
        assert cita.estado.nombre == 'pendiente'
        assert cita.motivo == 'Consulta general'
        assert str(cita) is not None

    def test_cita_default_estado(self, db, paciente, horario):
        """Cita should default estado to pendiente (pk=1)."""
        from citas.models import Cita
        cita = Cita.objects.create(
            paciente=paciente,
            medico=horario.medico,
            horario=horario,
            motivo='Dolor de cabeza',
        )
        assert cita.estado.nombre == 'pendiente'

    def test_cita_unique_horario(self, db, paciente, horario, estado_pendiente):
        """Duplicate horario should raise IntegrityError."""
        from citas.models import Cita
        Cita.objects.create(
            paciente=paciente, medico=horario.medico,
            horario=horario, estado=estado_pendiente,
            motivo='Primera cita',
        )
        with pytest.raises(IntegrityError):
            Cita.objects.create(
                paciente=paciente, medico=horario.medico,
                horario=horario, estado=estado_pendiente,
                motivo='Segunda cita',
            )

    def test_cita_audit_timestamps(self, db, paciente, horario):
        """Cita should have created_at and updated_at via BaseModel."""
        from citas.models import Cita
        cita = Cita.objects.create(
            paciente=paciente, medico=horario.medico,
            horario=horario, motivo='Control',
        )
        assert cita.created_at is not None
        assert cita.updated_at is not None


# ─── Model: AuditoriaCita ────────────────────────────────────────────────────

class TestAuditoriaCitaModel:
    """Tests for AuditoriaCita model."""

    def test_create_auditoria(self, db, cita, admin_user):
        """Creating a valid AuditoriaCita should succeed."""
        from citas.models import AuditoriaCita, EstadoCita
        pendiente = EstadoCita.objects.get(nombre='pendiente')
        confirmada = EstadoCita.objects.get(nombre='confirmada')
        auditoria = AuditoriaCita.objects.create(
            cita=cita,
            estado_anterior=pendiente,
            estado_nuevo=confirmada,
            cambiado_por=admin_user,
            nota='Paciente confirmó la cita',
        )
        assert auditoria.cita == cita
        assert auditoria.estado_anterior.nombre == 'pendiente'
        assert auditoria.estado_nuevo.nombre == 'confirmada'
        assert auditoria.cambiado_por == admin_user
        assert auditoria.fecha_cambio is not None
        assert 'confirmó' in auditoria.nota


# ─── Signals: Cita Audit Trail ───────────────────────────────────────────────

class TestCitaAuditSignal:
    """Tests for Cita audit trail signal."""

    def test_crear_cita_crea_auditoria(self, db, paciente, horario, admin_user):
        """Creating a Cita should create an initial audit entry."""
        from citas.models import Cita, AuditoriaCita
        cita = Cita.objects.create(
            paciente=paciente, medico=horario.medico,
            horario=horario, motivo='Consulta',
        )
        auditorias = AuditoriaCita.objects.filter(cita=cita)
        assert auditorias.count() == 1
        aud = auditorias.first()
        assert aud.estado_anterior is None
        assert aud.estado_nuevo.nombre == 'pendiente'

    def test_cambio_estado_crea_auditoria(self, db, cita, admin_user):
        """Changing Cita estado should create a new audit entry."""
        from citas.models import AuditoriaCita, EstadoCita
        confirmada = EstadoCita.objects.get(nombre='confirmada')
        cita.estado = confirmada
        cita.save()
        assert AuditoriaCita.objects.filter(cita=cita).count() == 2

    def test_multiple_cambios_crean_auditorias(self, db, cita, admin_user):
        """Multiple state changes should create multiple audit entries."""
        from citas.models import AuditoriaCita, EstadoCita
        confirmada = EstadoCita.objects.get(nombre='confirmada')
        realizada = EstadoCita.objects.get(nombre='realizada')

        cita.estado = confirmada
        cita.save()

        cita.estado = realizada
        cita.save()

        auditorias = AuditoriaCita.objects.filter(cita=cita).order_by('fecha_cambio')
        assert auditorias.count() == 3
        assert auditorias[0].estado_nuevo.nombre == 'pendiente'
        assert auditorias[1].estado_nuevo.nombre == 'confirmada'
        assert auditorias[2].estado_nuevo.nombre == 'realizada'

    def test_sin_cambio_no_auditoria(self, db, cita, admin_user):
        """Saving Cita without changing estado should NOT create audit entry."""
        from citas.models import AuditoriaCita
        cita.notas = 'Actualizando notas'
        cita.save()
        # Should still be 1 (initial) - no new audit for nota change
        assert AuditoriaCita.objects.filter(cita=cita).count() == 1


# ─── Fixtures for API tests ─────────────────────────────────────────────────

@pytest.fixture
def admin_client(db, test_admin_user):
    """Provide an authenticated admin API client."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=test_admin_user)
    return client


@pytest.fixture
def paciente_client(db, paciente_usuario):
    """Provide an authenticated paciente API client."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=paciente_usuario)
    return client


@pytest.fixture
def available_horario(db, medico):
    """Create an available Horario."""
    from medicos.models import Horario
    return Horario.objects.create(
        medico=medico,
        fecha=date.today() + timedelta(days=5),
        hora_inicio=time(14, 0),
        hora_fin=time(15, 0),
    )


@pytest.fixture
def past_horario(db, medico):
    """Create a Horario in the past (for 24h window test)."""
    from medicos.models import Horario
    return Horario.objects.create(
        medico=medico,
        fecha=date.today() - timedelta(days=1),
        hora_inicio=time(9, 0),
        hora_fin=time(10, 0),
    )


# ─── API: Serializers ───────────────────────────────────────────────────────

class TestCitaSerializer:
    """Tests for CitaSerializer."""

    def test_serialize_cita(self, db, cita):
        """Serializer should return correct fields."""
        from citas.serializers import CitaSerializer
        serializer = CitaSerializer(cita)
        assert 'id' in serializer.data
        assert 'paciente' in serializer.data


# ─── API: Views — Cita CRUD ────────────────────────────────────────────────

class TestCitaBookEndpoint:
    """Tests for POST /api/citas/ (book appointment)."""

    BOOK_URL = '/api/citas/'

    def test_book_success(self, paciente_client, db, paciente, available_horario):
        """Booking should create Cita and set horario.disponible=False."""
        response = paciente_client.post(self.BOOK_URL, {
            'paciente': paciente.id,
            'medico': available_horario.medico_id,
            'horario': available_horario.id,
            'motivo': 'Consulta general',
        }, format='json')
        assert response.status_code == 201
        assert response.data['estado_nombre'] == 'pendiente'
        # Verify horario is no longer available
        available_horario.refresh_from_db()
        assert available_horario.disponible is False

    def test_book_unauthenticated(self, api_client, db, paciente, available_horario):
        """Unauthenticated user should get 401."""
        response = api_client.post(self.BOOK_URL, {
            'paciente': paciente.id,
            'medico': available_horario.medico_id,
            'horario': available_horario.id,
            'motivo': 'Consulta',
        }, format='json')
        assert response.status_code == 401

    def test_book_already_booked(self, paciente_client, db, paciente, available_horario):
        """Booking an already booked horario should fail."""
        # First booking
        paciente_client.post(self.BOOK_URL, {
            'paciente': paciente.id,
            'medico': available_horario.medico_id,
            'horario': available_horario.id,
            'motivo': 'Primera',
        }, format='json')
        # Second booking - should fail
        response = paciente_client.post(self.BOOK_URL, {
            'paciente': paciente.id,
            'medico': available_horario.medico_id,
            'horario': available_horario.id,
            'motivo': 'Segunda',
        }, format='json')
        assert response.status_code == 400


class TestCitaCancelEndpoint:
    """Tests for POST /api/citas/{id}/cancelar/."""

    def test_cancel_success(self, paciente_client, db, paciente, available_horario):
        """Cancelling should update estado and set horario.disponible=True."""
        from citas.models import Cita
        # Book first
        book_resp = paciente_client.post('/api/citas/', {
            'paciente': paciente.id,
            'medico': available_horario.medico_id,
            'horario': available_horario.id,
            'motivo': 'A cancelar',
        }, format='json')
        cita_id = book_resp.data['id']

        # Cancel
        cancel_resp = paciente_client.post(f'/api/citas/{cita_id}/cancelar/', {}, format='json')
        assert cancel_resp.status_code == 200

        # Verify estado changed
        cita = Cita.objects.get(id=cita_id)
        assert cita.estado.nombre == 'cancelada'
        # Verify horario is available again
        available_horario.refresh_from_db()
        assert available_horario.disponible is True

    def test_cancel_past_appointment(self, paciente_client, db, paciente, past_horario):
        """Cancelling a past appointment (outside 24h window) should fail."""
        # Past horario means the appointment is already in the past
        from citas.models import Cita, EstadoCita
        pendiente = EstadoCita.objects.get(nombre='pendiente')
        cita = Cita.objects.create(
            paciente=paciente, medico=past_horario.medico,
            horario=past_horario, estado=pendiente,
            motivo='Cita pasada',
        )
        response = paciente_client.post(f'/api/citas/{cita.id}/cancelar/', {}, format='json')
        assert response.status_code == 400


class TestCitaListEndpoint:
    """Tests for GET /api/citas/."""

    LIST_URL = '/api/citas/'

    def test_list_authenticated(self, paciente_client, db, cita):
        """Authenticated user should list citas."""
        response = paciente_client.get(self.LIST_URL, format='json')
        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_list_unauthenticated(self, api_client, db):
        """Unauthenticated user should get 401."""
        response = api_client.get(self.LIST_URL, format='json')
        assert response.status_code == 401


class TestCitaDetailEndpoint:
    """Tests for GET /api/citas/{id}/."""

    def test_detail(self, paciente_client, db, cita):
        """Authenticated user should view a cita."""
        response = paciente_client.get(f'/api/citas/{cita.id}/', format='json')
        assert response.status_code == 200
