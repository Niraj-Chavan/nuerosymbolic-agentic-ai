"""
Celery Beat Schedule
=====================
Periodic task definitions for the Celery Beat scheduler.
"""

from __future__ import annotations

from celery.schedules import crontab

beat_schedule = {
    # ---------------------------------------------------------------
    # 1. Clean up expired sessions every day at 2:00 AM UTC
    # ---------------------------------------------------------------
    "cleanup-old-sessions": {
        "task": "app.workers.tasks.cleanup_old_sessions",
        "schedule": crontab(hour=2, minute=0),
        "options": {"expires": 3600},
    },

    # ---------------------------------------------------------------
    # 2. Refresh concept mastery cache every 6 hours
    # ---------------------------------------------------------------
    "update-concept-mastery-cache": {
        "task": "app.workers.tasks.update_concept_mastery_cache",
        "schedule": crontab(hour="*/6", minute=0),
        "options": {"expires": 1800},
    },

    # ---------------------------------------------------------------
    # 3. Generate daily quiz recommendations at 8:00 AM UTC
    # ---------------------------------------------------------------
    "generate-daily-quiz-recommendations": {
        "task": "app.workers.tasks.generate_daily_quiz_recommendations",
        "schedule": crontab(hour=8, minute=0),
        "options": {"expires": 3600},
    },

    # ---------------------------------------------------------------
    # 4. Archive old operation history weekly (Sunday 3:00 AM UTC)
    # ---------------------------------------------------------------
    "archive-old-operation-history": {
        "task": "app.workers.tasks.archive_old_operation_history",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
        "options": {"expires": 7200},
    },
}
