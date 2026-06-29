#!/usr/bin/env bash
set -e

export DB_ENGINE=django.db.backends.sqlite3
export DB_NAME=db.sqlite3

echo "→ Aplicando migraciones..."
python manage.py migrate

echo "→ Cargando datos iniciales..."
python manage.py load_initial_data

echo ""
echo "→ Servidor listo en http://127.0.0.1:8000"
echo ""
python manage.py runserver
