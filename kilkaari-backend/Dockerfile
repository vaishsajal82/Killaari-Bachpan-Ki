# kilkaari-backend/Dockerfile
FROM python:3.12-slim

# Prevents Python from writing .pyc files / buffering stdout — cleaner logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps needed to build psycopg2 (PostgreSQL driver) from source if a
# prebuilt wheel isn't available for this base image's architecture
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (separate layer so `docker build` reuses the
# cache when only app code changes, not requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual application code
COPY . .
RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
