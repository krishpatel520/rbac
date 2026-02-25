#!/bin/sh
set -e

echo ">>> [RBAC] Starting entrypoint..."

# ----------------------------------------------------------------
# Wait for PostgreSQL to be ready
# ----------------------------------------------------------------
DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo ">>> [RBAC] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

until nc -z "$DB_HOST" "$DB_PORT"; do
  echo ">>> [RBAC] PostgreSQL not yet available — retrying in 2s..."
  sleep 2
done

echo ">>> [RBAC] PostgreSQL is up!"

# ----------------------------------------------------------------
# Run Django migrations
# ----------------------------------------------------------------
echo ">>> [RBAC] Running database migrations..."
python manage.py migrate --noinput

# ----------------------------------------------------------------
# Collect static files (needed for Django Admin in Docker)
# ----------------------------------------------------------------
python manage.py collectstatic --noinput

# ----------------------------------------------------------------
# Execute the main process (CMD from Dockerfile)
# ----------------------------------------------------------------
echo ">>> [RBAC] Starting application..."
exec "$@"
