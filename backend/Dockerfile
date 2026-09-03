# backend/Dockerfile
#
# Production-ish image for the Flask API. Used by docker-compose for local
# dev, and as the basis for deploying to any container host (Render,
# Railway, Fly.io, ECS, etc.) for production.

FROM python:3.12-slim

WORKDIR /app

# System deps needed to build psycopg2-binary's dependencies on slim images
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# gunicorn, not `python run.py` -- Flask's dev server is single-threaded
# and not meant to handle concurrent real users.
#
# Runs `flask db upgrade` before starting the server so schema migrations
# apply automatically on every deploy (idempotent -- a no-op if already
# up to date). Binds to $PORT when the host provides one (Railway assigns
# this dynamically) and falls back to 5000 for docker-compose / local use,
# where the port is not set.
CMD ["sh", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 3 run:app"]
