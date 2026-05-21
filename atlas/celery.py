"""Celery app for the atlas project.

Auto-discovers `tasks.py` modules in any installed app.
"""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'atlas.settings')

app = Celery('atlas')

# Pull config from Django settings, using keys prefixed with `CELERY_`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Find tasks.py in every INSTALLED_APP.
app.autodiscover_tasks()
