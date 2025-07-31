from .celery_app import app_celery
from .config import settings
from .duck_db import conn_duckdb, insert_payment, get_payments_summary, purge_payments, init_database

init_database()

__all__ = [
    "settings",
    "app_celery",
    "conn_duckdb",
    "insert_payment",
    "get_payments_summary",
    "purge_payments",
]
