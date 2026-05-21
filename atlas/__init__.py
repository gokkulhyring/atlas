# Tell Django to use PyMySQL (pure-Python) as if it were `mysqlclient`.
# The version_info override placates Django's version check, which expects
# the mysqlclient version-tuple format.
import pymysql

pymysql.version_info = (1, 4, 6, "final", 0)
pymysql.install_as_MySQLdb()

# Make the Celery app discoverable as `atlas.celery_app` and ensure it loads
# whenever Django starts (so @shared_task decorators register on import).
from .celery import app as celery_app  # noqa: E402

__all__ = ('celery_app',)
