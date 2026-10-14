"""
Centralized Configuration
==========================
All environment variables are read once here.
Never read os.getenv() directly anywhere else.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # --- App ---
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    debug: bool = environment == "development"

    # --- CORS ---
    cors_origins: List[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    )

    # --- LLM ---
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # --- Database ---
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./ai_tree_tutor.db",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- Celery ---
    celery_broker_url: str = os.getenv(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/1",
    )
    celery_result_backend: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/2",
    )

    # --- Async ---
    async_ai_generation: bool = os.getenv("ASYNC_AI_GENERATION", "false").lower() == "true"
    task_timeout_seconds: int = int(os.getenv("TASK_TIMEOUT_SECONDS", "120"))

    # --- Quiz ---
    max_questions_per_quiz: int = int(os.getenv("MAX_QUESTIONS_PER_QUIZ", "20"))
    default_quiz_size: int = int(os.getenv("DEFAULT_QUIZ_SIZE", "5"))

    # --- Cache TTLs (seconds) ---
    cache_ttl_validation: int = int(os.getenv("CACHE_TTL_VALIDATION", "300"))      # 5 min
    cache_ttl_concepts: int = int(os.getenv("CACHE_TTL_CONCEPTS", "600"))           # 10 min
    cache_ttl_quiz: int = int(os.getenv("CACHE_TTL_QUIZ", "3600"))                  # 1 hour
    cache_ttl_complexity: int = int(os.getenv("CACHE_TTL_COMPLEXITY", "600"))       # 10 min


settings = Settings()
