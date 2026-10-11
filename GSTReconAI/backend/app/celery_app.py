"""Celery application binding for reconciliation jobs.

Celery is optional: it is only used when REDIS_URL (or CELERY_BROKER_URL) is configured.
Run a worker with:  celery -A app.celery_app.celery_app worker -Q reconciliation --loglevel=info
"""
from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "gst_recon_ai",
    broker=settings.broker_url,
    # Job state lives in the database, so a result backend is optional (off by default).
    backend=settings.celery_result_backend,
    include=["app.services.recon_engine"],
)
celery_app.conf.task_routes = {"app.services.recon_engine.*": {"queue": "reconciliation"}}
celery_app.conf.timezone = "Asia/Kolkata"
celery_app.conf.task_ignore_result = True
celery_app.conf.broker_connection_retry_on_startup = True
# Fail fast when publishing so the API can fall back to in-process execution if Redis is down.
celery_app.conf.broker_connection_timeout = 3
celery_app.conf.task_publish_retry_policy = {
    "max_retries": 1,
    "interval_start": 0,
    "interval_step": 0.5,
    "interval_max": 0.5,
}
celery_app.conf.broker_transport_options = {"socket_connect_timeout": 3}

__all__ = ["celery_app"]
