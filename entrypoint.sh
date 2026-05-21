#!/bin/sh
# Container entrypoint: bring the DB schema up to date and collect static files,
# then hand off to whatever command was passed (gunicorn by default).
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
