import pytest
from django.urls import reverse
from django.test import Client

from accounts.models import Usuario, Paciente
from medicos import models as medicos_models
from especialidades.models import Especialidad
from citas.models import Cita, EstadoCita
from expedientes.models import Expediente
from notificaciones.models import Notificacion


# ─── Helpers ───────────────────────────────────────────────────────────────

@pytest.fixture
def admin_user(db):
    return Usuario.objects.create_user(
        correo='admin@test.com', password='Admin123!',
        nombre='Admin', apellido='User', rol='admin', is_staff=True,
    )


@pytest.fixture
def paciente_user(db):
    return Usuario.objects.create_user(
        correo='paciente@test.com', password='Paciente1!',
        nombre='Paciente', apellido='Test', rol='paciente',
    )


@pytest.fixture
def medico_user(db):
    return Usuario.objects.create_user(
        correo='medico@test.com', password='Medico1!',
        nombre='Medico', apellido='Test', rol='medico',
    )


@pytest.fixture
def paciente(db, paciente_user):
    return Paciente.objects.get(usuario=paciente_user)


@pytest.fixture
def medico(db, medico_user, especialidad):
    m = medicos_models.Medico.objects.create(
        usuario=medico_user,
    )
    m.especialidades.create(especialidad=especialidad, es_principal=True)
    return m


@pytest.fixture
def especialidad(db):
    return Especialidad.objects.create(nombre='Cardiología', activo=True)


@pytest.fixture
def estado_pendiente(db):
    return EstadoCita.objects.get(nombre='pendiente')


@pytest.fixture
def horario(db, medico):
    return medicos_models.Horario.objects.create(
        medico=medico, fecha='2026-12-01',
        hora_inicio='10:00', hora_fin='10:30', disponible=True,
    )


@pytest.fixture
def cita(db, paciente, medico, horario, estado_pendiente):
    return Cita.objects.create(
        paciente=paciente, medico=medico, horario=horario,
        estado=estado_pendiente, motivo='Control',
    )


@pytest.fixture
def expediente(db, paciente, medico, cita):
    return Expediente.objects.create(
        paciente=paciente, medico=medico,
        cita=cita, diagnostico='Diagnóstico de prueba',
    )


def login_client(client, user):
    client.login(correo=user.correo, password={
        'admin': 'Admin123!', 'paciente': 'Paciente1!', 'medico': 'Medico1!',
    }[user.rol])


# ─── Expedientes Frontend ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestExpedientesFrontend:
    def test_lista_requires_login(self, client):
        r = client.get(reverse('expedientes:lista'))
        assert r.status_code == 302

    def test_paciente_ve_sus_expedientes(self, client, paciente_user, expediente):
        client.force_login(paciente_user)
        r = client.get(reverse('expedientes:lista'))
        assert r.status_code == 200
        assert 'Diagnóstico de prueba' in r.content.decode()

    def test_medico_ve_sus_expedientes(self, client, medico_user, expediente):
        client.force_login(medico_user)
        r = client.get(reverse('expedientes:lista'))
        assert r.status_code == 200
        assert 'Diagnóstico de prueba' in r.content.decode()

    def test_crear_get_medico(self, client, medico_user):
        client.force_login(medico_user)
        r = client.get(reverse('expedientes:crear'))
        assert r.status_code == 200

    def test_crear_get_paciente_denied(self, client, paciente_user):
        client.force_login(paciente_user)
        r = client.get(reverse('expedientes:crear'))
        assert r.status_code == 302

    def test_crear_post_medico(self, client, medico_user, paciente):
        medicos_models.Medico.objects.create(usuario=medico_user)
        client.force_login(medico_user)
        r = client.post(reverse('expedientes:crear'), {
            'paciente': paciente.pk,
            'diagnostico': 'Nuevo dx',
            'tratamiento': 'Reposo',
        })
        assert r.status_code == 302, r.content.decode()[:500]
        assert Expediente.objects.filter(diagnostico='Nuevo dx').exists()


# ─── Notificaciones Frontend ───────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionesFrontend:
    def test_lista_requires_login(self, client):
        r = client.get(reverse('notificaciones:lista'))
        assert r.status_code == 302

    def test_lista_muestra_notificaciones(self, client, paciente_user):
        Notificacion.objects.create(
            usuario=paciente_user, tipo='sistema',
            titulo='Test', mensaje='Mensaje test',
        )
        client.force_login(paciente_user)
        r = client.get(reverse('notificaciones:lista'))
        assert r.status_code == 200
        assert 'Test' in r.content.decode()

    def test_no_leidas_api(self, client, paciente_user):
        Notificacion.objects.create(
            usuario=paciente_user, tipo='sistema',
            titulo='Test', mensaje='Test', leida=False,
        )
        client.force_login(paciente_user)
        r = client.get(reverse('notificaciones:no_leidas_api'))
        assert r.status_code == 200
        assert r.json()['no_leidas'] == 1

    def test_recientes_api(self, client, paciente_user):
        Notificacion.objects.create(
            usuario=paciente_user, tipo='sistema',
            titulo='Reciente', mensaje='Test',
        )
        client.force_login(paciente_user)
        r = client.get(reverse('notificaciones:recientes_api'))
        assert r.status_code == 200
        assert len(r.json()) == 1


# ─── Admin Usuarios Frontend ───────────────────────────────────────────────

@pytest.mark.django_db
class TestAdminUsuariosFrontend:
    def test_lista_requires_staff(self, client, paciente_user):
        client.force_login(paciente_user)
        r = client.get(reverse('admin-usuarios'))
        assert r.status_code == 302

    def test_lista_muestra_usuarios(self, client, admin_user, paciente_user):
        client.force_login(admin_user)
        r = client.get(reverse('admin-usuarios'))
        assert r.status_code == 200
        assert 'paciente@test.com' in r.content.decode()

    def test_bloquear_usuario(self, client, admin_user, paciente_user):
        client.force_login(admin_user)
        r = client.post(reverse('admin-usuario-bloquear-frontend', args=[paciente_user.pk]))
        assert r.status_code == 302
        assert not Usuario.objects.get(pk=paciente_user.pk).is_active

    def test_activar_usuario(self, client, admin_user, paciente_user):
        paciente_user.is_active = False
        paciente_user.save()
        client.force_login(admin_user)
        r = client.post(reverse('admin-usuario-activar-frontend', args=[paciente_user.pk]))
        assert r.status_code == 302
        assert Usuario.objects.get(pk=paciente_user.pk).is_active

    def test_eliminar_usuario(self, client, admin_user, paciente_user):
        client.force_login(admin_user)
        r = client.post(reverse('admin-usuario-eliminar-frontend', args=[paciente_user.pk]))
        assert r.status_code == 302
        assert not Usuario.objects.filter(pk=paciente_user.pk).exists()

    def test_no_eliminar_admin(self, client, admin_user):
        client.force_login(admin_user)
        r = client.post(reverse('admin-usuario-eliminar-frontend', args=[admin_user.pk]))
        assert r.status_code == 302
        assert Usuario.objects.filter(pk=admin_user.pk).exists()


# ─── Notificación signal tests ─────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionSignals:
    def test_cita_creada_crea_notificacion(self, client, paciente_user, medico_user, paciente, medico, horario):
        estado = EstadoCita.objects.get(nombre='pendiente')
        horario.disponible = False
        horario.save()
        Cita.objects.create(
            paciente=paciente, medico=medico, horario=horario,
            estado=estado, motivo='Control',
        )
        assert Notificacion.objects.filter(usuario=paciente_user, tipo='cita_confirmada').exists()

    def test_cita_cancelada_crea_notificaciones(self, db, paciente_user, medico_user, cita):
        cancelada = EstadoCita.objects.get(nombre='cancelada')
        cita.estado = cancelada
        cita.save(update_fields=['estado'])

        assert Notificacion.objects.filter(usuario=paciente_user, tipo='cita_cancelada').exists()
        assert Notificacion.objects.filter(usuario=medico_user, tipo='cita_cancelada').exists()
