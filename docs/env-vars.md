# Variables de entorno

Todas se configuran vía `.env` o export. Sin ninguna, el proyecto arranca en modo dev con defaults.

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | *(fallback dev)* | Secret key de producción |
| `DJANGO_DEBUG` | `True` | `False` en producción |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Separado por comas |
| `DB_ENGINE` | `django.db.backends.mysql` | Usar `django.db.backends.sqlite3` para dev |
| `DB_NAME` | `medisync` | Nombre de la base |
| `DB_USER` | `medisync` | Usuario de DB |
| `DB_PASSWORD` | `medisync` | Contraseña de DB |
| `DB_HOST` | `localhost` | Host de DB |
| `DB_PORT` | `3306` | Puerto de DB |
| `EMAIL_BACKEND` | `console.EmailBackend` | `smtp.EmailBackend` en producción |
| `EMAIL_HOST` | `""` | SMTP host |
| `EMAIL_PORT` | `587` | SMTP puerto |
| `EMAIL_USE_TLS` | `True` | TLS on/off |
| `EMAIL_HOST_USER` | `""` | SMTP usuario |
| `EMAIL_HOST_PASSWORD` | `""` | SMTP contraseña |
| `DEFAULT_FROM_EMAIL` | `noreply@medisync.com` | Remitente de emails |

> **Dev rápido**: `cp .env.example .env` y dejá `DB_ENGINE=django.db.backends.sqlite3`, no necesitás MySQL corriendo.
