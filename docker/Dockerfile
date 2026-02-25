FROM python:3.11-slim

# ----------------------------------------------------------------
# ENVIRONMENT
# All runtime config is injected at container start via environment
# variables / docker-compose. Only build-time constants live here.
# ----------------------------------------------------------------
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ----------------------------------------------------------------
# SYSTEM DEPENDENCIES
# libpq-dev        → psycopg2 (PostgreSQL)
# build-essential  → C extensions
# netcat-openbsd   → health-check in entrypoint (nc -z)
# curl             → optional debugging; remove in hardened prod images
# ----------------------------------------------------------------
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    netcat-openbsd; \
    rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------------
# WORKDIR
# ----------------------------------------------------------------
WORKDIR /app

# ----------------------------------------------------------------
# PYTHON DEPENDENCIES
# Copy manifests first — Docker caches this layer until files change.
# ----------------------------------------------------------------
COPY requirements.txt ./

RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------
# APPLICATION CODE
# ----------------------------------------------------------------
COPY . /app/

# ----------------------------------------------------------------
# ENTRYPOINT
# ----------------------------------------------------------------
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# ----------------------------------------------------------------
# EXPOSE
# ----------------------------------------------------------------
EXPOSE 8002

# ----------------------------------------------------------------
# START SERVICE
# Uses gunicorn.conf.py for all tuning (workers, timeouts, logging).
# ----------------------------------------------------------------
CMD ["gunicorn", "-c", "gunicorn.conf.py", "rbac_project.wsgi:application"]
