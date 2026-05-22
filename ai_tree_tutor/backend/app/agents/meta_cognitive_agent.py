from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional
from app.llm.base_llm import LLMInterface
from app.agents.concept_graph_agent import ConceptGraphAgent
from app.agents.emotional_tracker import EmotionalStateTracker

logger = logging.getLogger(__name__)

class MetaCognitiveAgent:
    """
    Orchestrates the multi-agent Socratic tutoring system.
    Tracks teaching cycles, selects pedagogical strategies, checks response patterns,
    and switches modalities dynamically if the student is stuck.
    """
    def __init__(
        self,
        llm: LLMInterface,
        concept_agent: ConceptGraphAgent,
        emotional_tracker: EmotionalStateTracker
    ):
        self.llm = llm
        self.concept_agent = concept_agent
        self.emotional_tracker = emotional_tracker
        # Maps session_id -> list of teaching choices / metadata
        self._decisions: Dict[str, List[Dict[str, Any]]] = {}

    def get_session_decisions(self, session_id: str) -> List[Dict[str, Any]]:
        return self._decisions.get(session_id, [])

    def record_decision(self, session_id: str, decision: Dict[str, Any]):
        if session_id not in self._decisions:
            self._decisions[session_id] = []
        self._decisions[session_id].append(decision)

    async def decide_strategy(
        self,
        session_id: str,
        concept_id: str,
        emotional_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determines the pedagogical strategy (socratic, analogy, example, visual)
        and choice details based on student emotional tracker and mastery data.
        """
        concept_data = self.concept_agent.get_concept_data(concept_id)
        mastery = concept_data["mastery"] if concept_data else 0.5
        
        # Analyze historical cycles for this session
        history = self.get_session_decisions(session_id)
        consecutive_failures = sum(
            1 for d in history[-3:] if d.get("outcome") == "incorrect"
        )
        
        # Default strategy selection rules
        strategy = "socratic_questioning"
        reason = "Standard learning modality chosen for guidance."
        
        if emotional_state.get("sentiment") == "frustrated" or consecutive_failures >= 2:
            strategy = "analogy_based"
            reason = "Student shows frustration or repeating mistakes; switching to a descriptive analogy to ease understanding."
        elif emotional_state.get("cognitive_load") == "overload":
            strategy = "example_driven"
            reason = "High cognitive load detected; showing concrete worked step-by-step examples."
        elif mastery > 0.7:
            strategy = "socratic_questioning"
            reason = "Student shows high mastery; using probing Socratic questions to encourage self-explanation."
        elif consecutive_failures == 1:
            strategy = "visual_demonstration"
            reason = "First incorrect answer; generating dynamic visual SVG description for intuitive learning."

        decision = {
            "concept_id": concept_id,
            "strategy": strategy,
            "reason": reason,
            "consecutive_failures": consecutive_failures,
            "mastery": mastery,
            "outcome": "pending"  # Will be updated on verify
        }
        self.record_decision(session_id, decision)
        return decision

    async def generate_response(
        self,
        session_id: str,
        concept_id: str,
        student_message: str,
        history: List[Dict[str, str]],
        strategy: str
    ) -> Dict[str, Any]:
        """
        Generates Socratic tutoring responses leveraging the chosen pedagogical strategy.
        Returns a dictionary containing 'response', 'repaired', and 'widget'.
        """
        concept_data = self.concept_agent.get_concept_data(concept_id)
        concept_name = concept_data["name"] if concept_data else concept_id
        false_belief = concept_data["false_belief"] if concept_data and "false_belief" in concept_data else ""
        
        history_str = ""
        for h in history[-6:]:
            role = "Student" if h.get("role") == "user" else "Tutor"
            history_str += f"{role}: {h.get('content')}\n"

        prompt = f"""You are a Socratic Data Structures Tutor specializing in tree structures.
        Respond to the student's question/message.
        
        CURRENT Pedagogy Strategy: {strategy.upper()}
        (Options: SOCRATIC_QUESTIONING, ANALOGY_BASED, EXAMPLE_DRIVEN, VISUAL_DEMONSTRATION)
        
        GROUNDING RULES:
        1. NEVER give the direct answer or write complete code blocks.
        2. If strategy is ANALOGY_BASED, start with a rich, simple real-world analogy.
        3. If strategy is EXAMPLE_DRIVEN, work through a small concrete numbers list trace.
        4. If strategy is VISUAL_DEMONSTRATION, generate a beautiful HTML/SVG widget or description explaining the tree structure nodes and relations visually.
        5. If strategy is SOCRATIC_QUESTIONING, ask guidance questions to prompt them.
        6. Keep replies brief: 3-4 sentences max.
        7. Always end with a Socratic guiding question unless the concept has been successfully repaired.
        
        CONTEXT:
        Target Concept: {concept_name} (ID: {concept_id})
        Common misconception to avoid: {false_belief}
        
        RECENT CHAT HISTORY:
        {history_str}
        Student message: "{student_message}"
        
        Provide the response in EXACT JSON format with the following keys:
        {{
          "response": "Your Socratic conversational response here.",
          "repaired": boolean, // Set to true ONLY IF the student has explicitly demonstrated full mastery, corrected their misconception, and understanding of the concept in their message. Otherwise false.
          "widget": {{
             "type": "html",
             "content": "A self-contained HTML block (with SVG or styled elements) if strategy is VISUAL_DEMONSTRATION or if a visual would help clarify the concept. Otherwise null."
          }} or null
        }}
        
        CONSTRAINTS:
        - Return ONLY valid JSON.
        - Do NOT wrap in markdown code fences like ```json.
        """

        if self.llm.available:
            try:
                result = self.llm._query(prompt)
                if isinstance(result, dict) and "response" in result:
                    # Enforce default fields
                    if "repaired" not in result:
                        result["repaired"] = False
                    if "widget" not in result:
                        result["widget"] = None
                    return result
                
                if isinstance(result, str):
                    text = result.strip()
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, dict) and "response" in parsed:
                            return {
                                "response": parsed["response"],
                                "repaired": parsed.get("repaired", False),
                                "widget": parsed.get("widget", None)
                            }
                    except Exception:
                        pass
            except Exception as e:
                logger.warning("MetaCognitiveAgent LLM generation failed: %s", e)

        # Fallback responses
        fallback_msg = "What property do you think is currently violated in this tree structure? Let's check the rules."
        if strategy == "analogy_based":
            fallback_msg = f"Think of {concept_name} like organizing books in a bookshelf. What happens if one shelf gets too heavy and falls over?"
        elif strategy == "example_driven":
            fallback_msg = f"Let's trace: if we insert keys [10, 20] and then insert 30, which element is the root of the tree and which side does it incline to?"
        elif strategy == "visual_demonstration":
            fallback_msg = f"Picture the root node. Left child is balance factor -1, right child is +1. Where does the height imbalance point?"

        return {
            "response": fallback_msg,
            "repaired": False,
            "widget": None
        }
