# Medisync — Gestión de Consultorios Médicos

SaaS web para administrar turnos, historias clínicas y la relación paciente-médico en consultorios privados. Autenticación por email, dashboard por rol (paciente/médico/admin), notificaciones y reportes.

---

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # ajustar DB y email si corresponde
python manage.py migrate
python manage.py load_initial_data
python manage.py runserver
```

Accedé a `http://localhost:8000` — el registro está en `/accounts/register/` y el login vía modal en la landing.

> **Tests**: `pytest` — corre contra SQLite in-memory.

---

## Roles del sistema

| Rol | Acceso |
|-----|--------|
| **Paciente** | Agenda turnos, ve sus citas, historial clínico, notificaciones |
| **Médico** | Gestiona horarios, confirma/cancela/realiza citas, crea expedientes |
| **Administrador** | Dashboard, gestión de usuarios, reportes operativos |

---

## Arquitectura

### Dual interface

```
┌─────────────────────────────────────────────────┐
│               Navegador (Bulma)                  │
├──────────────────────┬──────────────────────────┤
│   Frontend HTML       │   REST API              │
│   (session auth)      │   (JWT auth)            │
├──────────────────────┼──────────────────────────┤
│   Django Templates    │   DRF @api_view         │
│   + Django Auth       │   + SimpleJWT           │
└──────────────────────┴──────────────────────────┘
                      │
              ┌───────┴───────┐
              │   Models      │
              └───────────────┘
```

- **Frontend**: server-rendered HTML con Bulma CDN + CSS custom. Usa sesiones Django.
- **API REST**: DRF con JWT para integración/mobile.
- **Auth dual**: session-based para frontend, `Authorization: Bearer <jwt>` para API.

### Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Django 5 + DRF |
| Auth | django-sesame (magic links), SimpleJWT, email-based custom user |
| DB | MySQL (dev: SQLite vía env) |
| Frontend | Bulma CSS + vanilla JS |
| API docs | drf-spectacular (Swagger/ReDoc en `/api/schema/`) |
| Testing | pytest + pytest-django |
| Cache | LocMemCache (login lockout) |

---

## Apps

| App | Responsabilidad |
|-----|----------------|
| **core** | Base abstracta (`BaseModel`), landing page, reportes, middleware, utils (email, CUIT, lockout), PDF |
| **accounts** | Usuario custom (email auth), perfiles Paciente/Medico, register/login/profile, JWT, admin de usuarios |
| **especialidades** | CRUD de especialidades médicas (admin), listado público |
| **medicos** | Datos profesionales, honorarios, `MedicoEspecialidad`, `Horario`, disponibilidad |
| **citas** | Ciclo de vida del turno (reserva → confirmación → cancelación → checklist médico), auditoría, PDF comprobante |
| **expedientes** | Historia clínica (diagnóstico, tratamiento, notas) ligada a citas |
| **notificaciones** | Notificaciones in-app por tipo (confirmación, cancelación, recordatorio, nuevo expediente, sistema) |

---

## Models — mapa rápido

```
Usuario (email, nombre, apellido, rol, documento)
├── Paciente (obra_social, contacto_emergencia, fecha_nacimiento)
├── MedicoProfile (numero_matricula, bio)
│   └── MedicoPractice (precio_consulta, atencion_online, informacion_consultorio)
│       └── MedicoEspecialidad ──── Especialidad
│       └── Horario (fecha, hora_inicio, hora_fin, disponible)
├── TokenRecuperacion (password reset)
└── Notificacion (tipo, título, mensaje, leída)

Cita ──── Paciente, Medico, Horario, EstadoCita, AuditoriaCita
Expediente ──── Paciente, Medico, Cita, diagnóstico, tratamiento
```

---

## URLs — guía rápida

### Frontend público

| URL | Vista |
|-----|-------|
| `/` | Landing (Hero → Servicios → Médicos → Contacto → Sobre Nosotros → Testimonios → Footer) |
| `/accounts/register/` | Registro (split layout: 45% imagen + 55% formulario) |
| `/accounts/login/` | POST login (GET redirige a home — el login es modal) |
| `/especialidades/` | Listado público de especialidades |
| `/medicos/` | Listado público de médicos con filtro |
| `/medicos/<pk>/` | Detalle público del médico + disponibilidad |

### Frontend autenticado (dashboard)

| URL | Rol | Vista |
|-----|-----|-------|
| `/dashboard/` | * | Home del dashboard con cards de stats |
| `/citas/agendar/` | paciente | Wizard: especialidad → médico → horario → motivo |
| `/citas/mis-citas/` | paciente | Listado de turnos propios |
| `/medicos/mis-horarios/` | médico | Gestión de bloques horarios |
| `/medicos/citas-agendadas/` | médico | Turnos asignados + marcar realizada/no-asistió |
| `/expedientes/` | * | Listado de historias clínicas |
| `/expedientes/crear/` | médico/admin | Crear expediente |
| `/notificaciones/` | * | Centro de notificaciones |
| `/dashboard/usuarios/` | admin | CRUD de usuarios |
| `/reportes/` | admin | Reportes operativos |

### API REST (JWT)

| Endpoint | Métodos |
|----------|---------|
| `/api/auth/register/` | POST |
| `/api/auth/login/` | POST |
| `/api/auth/profile/` | GET, PUT, PATCH |
| `/api/auth/token/` | POST (JWT obtain) |
| `/api/auth/token/refresh/` | POST |
| `/api/especialidades/` | GET, POST |
| `/api/medicos/` | GET, POST |
| `/api/medicos/<pk>/disponibilidad/` | GET, POST |
| `/api/citas/` | GET, POST |
| `/api/citas/<pk>/cancelar/` | POST |
| `/api/citas/<pk>/comprobante/` | GET (PDF) |
| `/api/expedientes/` | GET, POST |
| `/api/notificaciones/` | GET, POST |
| `/api/admin/usuarios/` | GET |

> Documentación interactiva: `/api/schema/swagger-ui/`

---

## Frontend CSS

| Archivo | Lines | Propósito |
|---------|-------|-----------|
| `static/css/landing.css` | ~1650 | Paleta navy (`#0B4F7C`), variables `--l-*`, secciones landing, modal login, animaciones scroll |
| `static/css/custom.css` | ~750 | Design system dashboard, variables `--brand-*`, sidebar, cards, tabla slots, dropdown notificaciones |

Ambos se sirven por CDN de Bulma + override vía CSS nativo (sin SCSS).

---

## Auth flow

```
Registro
  └─ POST /accounts/register/ → crea Usuario + Paciente (o MedicoProfile + MedicoPractice si rol=médico)
  └─ login automático → redirect a dashboard

Login (modal)
  └─ POST /accounts/login/ → EmailAuthenticationForm (valida lockout, 3 intentos → 15 min)
  └─ success → redirect vía next param (dashboard por defecto)

Logout
  └─ GET /accounts/logout/ → redirect a home

Password reset
  └─ Django CBV estándar: reset → confirm → complete
```

---

## Tests

```bash
pytest                           # todos los tests
pytest -k "citas"                # filtrar por app
pytest --cov                     # cobertura (si pytest-cov instalado)
```

Config en `pytest.ini` + `conftest.py`. Usa `config.test_settings` (SQLite in-memory).

---

## Checklist para desarrollo

- [ ] Migraciones creadas (`makemigrations`) y aplicadas (`migrate`)
- [ ] Tests pasan (`pytest`)
- [ ] Endpoints cubiertos: API (DRF) + frontend (template views)
- [ ] Notificaciones se crean vía signals en los eventos clave
- [ ] Lockout de login testeable (3 intentos, 15 min)
- [ ] PDF de comprobante generable
- [ ] Permisos chequeados por rol (paciente/medico/admin decorators)
