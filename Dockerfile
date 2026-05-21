# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

# Don't write .pyc files; flush stdout/stderr so logs show up immediately.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps:
#   build-essential is only needed if any wheel has to compile from source.
#   We keep the image slim by removing the build deps after pip install.
WORKDIR /app

# Install Python deps first so this layer is cached when only app code changes.
COPY requirements.txt .
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && pip install -r requirements.txt \
 && apt-get purge -y build-essential \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Copy the rest of the project.
COPY . .

# Where the SQLite DB and (future) media files live. Mounted as a volume in
# docker-compose so data survives `docker compose down`.
RUN mkdir -p /data && chown -R 1000:1000 /data /app

# Run as a non-root user (uid 1000).
RUN useradd -u 1000 -m django
USER django

EXPOSE 8000

# entrypoint.sh runs migrate + collectstatic, then execs the CMD.
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "atlas.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
