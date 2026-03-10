#!/bin/sh
set -e
echo "=== Starting staff-service ==="
echo "Waiting for PostgreSQL..."
while ! python -c "import psycopg2; psycopg2.connect(host='$DB_HOST', port='$DB_PORT', dbname='$DB_NAME', user='$DB_USER', password='$DB_PASSWORD')" 2>/dev/null; do
  echo "PostgreSQL not ready, retrying in 2s..."
  sleep 2
done
echo "PostgreSQL is ready!"
python manage.py makemigrations --noinput 2>/dev/null || true
python manage.py migrate --noinput
if [ -f seed_data.py ]; then
  python seed_data.py
fi
echo "Starting server on 0.0.0.0:8000..."
exec python manage.py runserver 0.0.0.0:8000
