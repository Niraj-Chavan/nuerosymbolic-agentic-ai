from __future__ import annotations
import time
import json
import logging
from typing import Any, Dict, List, Optional
from app.llm.base_llm import LLMInterface

logger = logging.getLogger(__name__)

class EmotionalStateTracker:
    """
    Tracks and analyzes student engagement, sentiment, and cognitive load
    based on response history, reaction speed, hints used, and retry actions.
    """
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        # Maps session_id -> interaction history
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _get_session_data(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": [],
                "hints_used": 0,
                "retries": 0,
                "last_message_time": 0.0,
                "response_times": [],
            }
        return self._sessions[session_id]

    def record_hint(self, session_id: str):
        data = self._get_session_data(session_id)
        data["hints_used"] += 1

    def record_retry(self, session_id: str):
        data = self._get_session_data(session_id)
        data["retries"] += 1

    def record_message(self, session_id: str, role: str, content: str):
        data = self._get_session_data(session_id)
        now = time.time()
        
        # Calculate response time for student messages
        if role == "user" and data["last_message_time"] > 0:
            diff = now - data["last_message_time"]
            data["response_times"].append(diff)
            
        data["messages"].append({
            "role": role,
            "content": content,
            "timestamp": now
        })
        data["last_message_time"] = now

    async def analyze_session(self, session_id: str) -> Dict[str, Any]:
        data = self._get_session_data(session_id)
        
        # Default fallback values
        sentiment = "neutral"
        cognitive_load = "medium"
        engagement_level = 75
        needs_intervention = False
        intervention_reason = ""
        
        # Analyze using Gemini if available
        recent_student_messages = [
            m["content"] for m in data["messages"] if m["role"] == "user"
        ][-4:]
        
        if self.llm.available and recent_student_messages:
            prompt = f"""Analyze the following recent student messages from a tutoring session for sentiment, engagement, and cognitive load:
            
            Messages:
            {json.dumps(recent_student_messages, indent=2)}
            
            Detect:
            1. Sentiment / Emotional state: Choose exactly one of [excited, confident, neutral, confused, frustrated, bored].
            2. Cognitive load: Choose exactly one of [low, medium, high, overload].
            3. Engagement Level: An integer score between 0 and 100.
            
            Respond in EXACT JSON format with no other text or markdown block formatting:
            {{
              "sentiment": "confused",
              "cognitive_load": "high",
              "engagement_score": 50
            }}
            """
            try:
                res = self.llm._query(prompt)
                if isinstance(res, dict) and "sentiment" in res:
                    sentiment = res.get("sentiment", "neutral")
                    cognitive_load = res.get("cognitive_load", "medium")
                    engagement_level = res.get("engagement_score", 75)
            except Exception as e:
                logger.warning("Gemini emotional tracker analysis query failed: %s", e)

        # Apply simple rule-based overrides
        avg_response_time = (
            sum(data["response_times"]) / len(data["response_times"])
            if data["response_times"] else 0.0
        )
        
        if data["hints_used"] >= 3:
            engagement_level = max(30, engagement_level - 15)
            if cognitive_load == "low":
                cognitive_load = "medium"
        
        if data["retries"] >= 3:
            sentiment = "frustrated"
            cognitive_load = "overload"
            engagement_level = max(20, engagement_level - 20)
            
        if avg_response_time > 0 and avg_response_time < 3.0 and data["retries"] >= 2:
            sentiment = "frustrated"
            engagement_level = max(20, engagement_level - 15)
            
        # Intervention check
        if engagement_level < 50 or sentiment == "frustrated" or cognitive_load == "overload":
            needs_intervention = True
            if sentiment == "frustrated":
                intervention_reason = "student_frustrated"
            elif cognitive_load == "overload":
                intervention_reason = "cognitive_overload"
            else:
                intervention_reason = "low_engagement"
                
        return {
            "session_id": session_id,
            "sentiment": sentiment,
            "cognitive_load": cognitive_load,
            "engagement_level": int(engagement_level),
            "needs_intervention": needs_intervention,
            "intervention_reason": intervention_reason,
            "avg_response_time": round(avg_response_time, 2),
            "hints_used": data["hints_used"],
            "retries": data["retries"]
        }
