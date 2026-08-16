#!/bin/sh
# entrypoint.sh — applies any pending Alembic migrations, then starts uvicorn.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."
# ${PORT:-8000}: local docker-compose sets no PORT env var, so this falls
# back to 8000 (matching the "8000:8000" mapping in docker-compose.yml).
# If this Dockerfile is ever used on Render (or any platform that injects
# its own PORT), this respects that instead — hardcoding 8000 would
# silently fail to bind to the port the platform actually routes traffic
# to.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 2
