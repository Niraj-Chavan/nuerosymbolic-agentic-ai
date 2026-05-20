"""
Celery Application — Async Task Queue with Beat Schedule
===========================================================
Background worker configuration for offloading AI generation
and periodic maintenance tasks.
"""

from __future__ import annotations

from celery import Celery

from app.config import settings
from app.workers.beat_schedule import beat_schedule

celery_app = Celery(
    "ai_tree_tutor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.task_timeout_seconds,
    task_soft_time_limit=settings.task_timeout_seconds - 10,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule=beat_schedule,
)
