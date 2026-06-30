# Despliegue

## Preparar entorno

```bash
export DJANGO_SECRET_KEY="<generar clave>"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="medisync.com,www.medisync.com"
export DB_ENGINE=django.db.backends.mysql
export DB_NAME=medisync
export DB_USER=medisync
export DB_PASSWORD="<db-password>"
export DB_HOST=localhost
export DB_PORT=3306
export EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
export EMAIL_HOST=smtp.ejemplo.com
export EMAIL_PORT=587
export EMAIL_USE_TLS=True
export EMAIL_HOST_USER="noreply@medisync.com"
export EMAIL_HOST_PASSWORD="<email-password>"
```

## Build

```bash
python manage.py migrate
python manage.py load_initial_data
python manage.py collectstatic --noinput
```

## Servir

### Gunicorn + nginx

```bash
gunicorn config.wsgi:application --workers=4 --bind=unix:/tmp/medisync.sock
```

Config de nginx:

```
server {
    listen 80;
    server_name medisync.com;
    client_max_body_size 10M;

    location /static/ {
        alias /ruta/a/medisync/staticfiles/;
    }

    location /media/ {
        alias /ruta/a/medisync/media/;
    }

    location / {
        proxy_pass http://unix:/tmp/medisync.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd unit

```
[Unit]
Description=Medisync
After=network.target

[Service]
User=medisync
WorkingDirectory=/ruta/a/medisync
EnvironmentFile=/ruta/a/medisync/.env
ExecStart=/usr/bin/gunicorn config.wsgi:application --workers=4 --bind=unix:/tmp/medisync.sock
Restart=always

[Install]
WantedBy=multi-user.target
```
