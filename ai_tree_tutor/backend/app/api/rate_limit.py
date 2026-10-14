"""
Rate Limit Presets
====================
Shared constants used by RateLimitMiddleware.
"""

LIMIT_TREES = (30, 60)
LIMIT_QUIZ_GENERATE = (5, 3600)
LIMIT_QUIZ = (20, 60)
LIMIT_CONCEPTS = (60, 60)
LIMIT_ANALYSIS = (20, 60)
