# Base image: Debian 12 with Python 3.11
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=battery.settings

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    python3-psycopg2 \
    gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pip dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Bake in the git revision
ARG GIT_COMMIT
ENV GIT_COMMIT=$GIT_COMMIT

# Expose port
EXPOSE 8000

# Entrypoint
ENTRYPOINT "bin/entrypoint.sh"
