from __future__ import annotations

import json
import base64
import logging
from io import BytesIO
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.dependencies import (
    get_llm,
    get_concept_agent,
    get_emotional_tracker,
    get_meta_agent,
    get_diagnostic_agent,
    get_curriculum_agent,
)
from app.llm.base_llm import LLMInterface
from app.agents.concept_graph_agent import ConceptGraphAgent
from app.agents.adaptive_teaching_agent import AdaptiveTeachingAgent
from app.agents.diagnostic_intelligence_agent import DiagnosticIntelligenceAgent
from app.agents.curriculum_architect_agent import CurriculumArchitectAgent
from app.concept_graph.learning_path import LearningPathGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


class TutorChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    concept_id: Optional[str] = None
    session_id: str = "default"


class RemedyStartRequest(BaseModel):
    concept_id: str
    session_id: str = "default"


class RemedyVerifyRequest(BaseModel):
    concept_id: str
    is_correct: bool
    session_id: str = "default"


def get_fallback_remedy(concept_id: str, name: str, false_belief: str) -> dict:
    return {
        "concept_id": concept_id,
        "concept_name": name,
        "theory": f"The concept '{name}' is a key part of self-balancing search trees or heaps. We enforce specific invariants (mathematical rules) to guarantee that all search, insertion, and deletion operations remain efficient, running in O(log n) time. Neglecting this concept violates these invariants, degrading performance.",
        "false_belief_explanation": f"The belief '{false_belief}' is a common misconception. In computer science, tree data structures rely on strict mathematical properties to maintain correct ordering and performance characteristics.",
        "worked_example": {
            "setup": f"Consider a tree state undergoing a series of operations involving {name}.",
            "problem": "If we omit the balancing or ordering rule, the tree invariants are violated, leading to unbalanced branches or search path issues.",
            "solution": "Applying the correct sequence of rotation, recoloring, or heap restructuring restores the tree invariants."
        },
        "interactive_question": {
            "question": f"Which of the following describes the core purpose of maintaining {name} in a tree structure?",
            "options": [
                "To ensure operations take O(log n) time and the mathematical properties of the tree are satisfied.",
                "To reduce memory usage to O(1) space.",
                "It is purely optional and doesn't affect efficiency.",
                "To convert the hierarchical structure into a simple array."
            ],
            "correct_option_index": 0,
            "explanation": "Maintaining tree invariants is essential for keeping the tree balanced and operations running in logarithmic time."
        }
    }


@router.get("/weak-concepts")
async def get_weak_concepts_tutor(
    concept_agent: ConceptGraphAgent = Depends(get_concept_agent)
):
    return concept_agent.get_weak_concepts(threshold=0.5)


@router.post("/chat")
async def tutor_chat(
    req: TutorChatRequest,
    llm: LLMInterface = Depends(get_llm),
    concept_agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    if not llm.available:
        return {"response": "AI Socratic Tutor is currently offline. Please check your Gemini API key configuration."}

    history_str = ""
    for h in req.history[-6:]:
        role = "Student" if h.get("role") == "user" else "Tutor"
        history_str += f"{role}: {h.get('content')}\n"

    teaching_agent = AdaptiveTeachingAgent(llm)
    
    try:
        result = teaching_agent.teach_dynamically(history_str, req.message, req.concept_id)
        if result and result.get("repaired") and req.concept_id:
            for _ in range(3):
                concept_agent.record_success(req.concept_id)
        if result and isinstance(result, dict) and req.concept_id:
            result["new_mastery"] = concept_agent._get_mastery(req.concept_id).value
        return result
    except Exception as e:
        return {"response": f"Let's trace this step. What do you think happens to the tree's invariants when you run this operation? [Error: {str(e)}]"}


def get_concept_video_link(concept_id: str, concept_name: str) -> str:
    CONCEPT_VIDEOS = {
        # AVL Tree
        "avl_balance_factor": "https://www.youtube.com/watch?v=1QSyP8S-gQA",
        "avl_rotation_mechanics": "https://www.youtube.com/watch?v=Jm94REt_1sU",
        "avl_rotation_cases": "https://www.youtube.com/watch?v=vRwi_Uc5j5Q",
        "avl_height_update": "https://www.youtube.com/watch?v=1QSyP8S-gQA",
        "avl_insert": "https://www.youtube.com/watch?v=Jm94REt_1sU",
        "avl_delete": "https://www.youtube.com/watch?v=wLy77n26A6Y",
        # Red-Black Tree
        "rb_properties": "https://www.youtube.com/watch?v=PhY56LpPtS4",
        "rb_uncle_identification": "https://www.youtube.com/watch?v=A3JZinzkMpk",
        "rb_recoloring": "https://www.youtube.com/watch?v=PhY56LpPtS4",
        "rb_rotation_mechanics": "https://www.youtube.com/watch?v=qA02FWRtbdw",
        "rb_insert_fixup": "https://www.youtube.com/watch?v=5IBxA-yT-r4",
        "rb_delete_fixup": "https://www.youtube.com/watch?v=PhY56LpPtS4",
        # Heaps
        "heap_sift_up": "https://www.youtube.com/watch?v=t0Cq6tVNRBA",
        "heap_sift_down": "https://www.youtube.com/watch?v=t0Cq6tVNRBA",
        "heapify": "https://www.youtube.com/watch?v=HqPJF2L5h9U",
        # B-Tree
        "btree_node_split": "https://www.youtube.com/watch?v=aGPXSzWeF8w",
        "btree_cascading_split": "https://www.youtube.com/watch?v=aGPXSzWeF8w",
        "btree_merge": "https://www.youtube.com/watch?v=K1a2B81242Y",
        # Segment Tree
        "seg_build": "https://www.youtube.com/watch?v=QvgpIX4LyV0",
        "seg_range_query": "https://www.youtube.com/watch?v=QvgpIX4LyV0",
        "seg_range_update": "https://www.youtube.com/watch?v=rYBtViWXYeI",
    }
    if concept_id in CONCEPT_VIDEOS:
        return CONCEPT_VIDEOS[concept_id]
    
    query = f"Data structures {concept_name} tutorial".replace(" ", "+")
    return f"https://www.youtube.com/results?search_query={query}"


@router.post("/remedy/start")
async def remedy_start(
    req: RemedyStartRequest,
    llm: LLMInterface = Depends(get_llm),
    concept_agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    concept = concept_agent.taxonomy.get_concept(req.concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    video_url = get_concept_video_link(req.concept_id, concept.name)

    prompt = f"""You are an expert Socratic Data Structures Tutor. 
    Start a dynamic remediation session for the concept "{concept.name}" (ID: {req.concept_id}).
    
    Concept Common Misconception (False Belief): "{concept.false_belief}"
    
    Provide the response in EXACT JSON format with the following keys:
    {{
      "concept_id": "{req.concept_id}",
      "concept_name": "{concept.name}",
      "theory": "A comprehensive, beautifully formatted explanation (in Markdown) of the concept '{concept.name}'. Explain the core mathematical properties, invariants, rules, and step-by-step logic. Address why the common false belief ('{concept.false_belief}') is incorrect.",
      "message": "Your opening conversational message here. Welcoming the student, introducing the concept, and asking a guiding, Socratic opening question to gauge their understanding of this specific topic."
    }}
    
    CONSTRAINTS:
    - Return ONLY valid JSON.
    - Do NOT wrap in markdown code fences like ```json.
    """

    fallback_theory = f"""
### Understanding {concept.name}

The concept of **{concept.name}** is fundamental to ensuring efficient operations on tree-based data structures. 

#### Core Invariants & Rules
To maintain the efficiency of this data structure, we enforce specific invariants:
1. **Mathematical Order/Structure**: Restricts how nodes are arranged and traversed.
2. **Efficiency Guarantees**: Keeps height balanced to ensure O(log n) time complexity.

#### Addressing Common Misconceptions
* **Misconception**: "{concept.false_belief}"
* **Why it is wrong**: Tree data structures rely on strict mathematical properties. Over-simplifying or ignoring these rules breaks the invariants, causing search operations to degrade to linear time O(n) or yielding corrupt layouts.
"""

    try:
        if llm.available:
            result = llm._query(prompt)
            if result and "message" in result:
                if "theory" not in result or not result["theory"]:
                    result["theory"] = fallback_theory
                result["video_link"] = video_url
                return result
        
        return {
            "concept_id": req.concept_id,
            "concept_name": concept.name,
            "theory": fallback_theory,
            "video_link": video_url,
            "message": f"Let's work on the concept of {concept.name}. A common misconception is: {concept.false_belief}. What are your thoughts on why this might be incorrect?"
        }
    except Exception:
        return {
            "concept_id": req.concept_id,
            "concept_name": concept.name,
            "theory": fallback_theory,
            "video_link": video_url,
            "message": f"Let's work on the concept of {concept.name}. A common misconception is: {concept.false_belief}. What are your thoughts on why this might be incorrect?"
        }


@router.post("/remedy/verify")
async def remedy_verify(
    req: RemedyVerifyRequest,
    concept_agent: ConceptGraphAgent = Depends(get_concept_agent),
):
    if req.is_correct:
        concept_agent.record_success(req.concept_id)
    else:
        concept_agent.record_mistake(req.concept_id)

    progress_summary = concept_agent.get_progress_summary()
    mastery_value = 0.5
    for c in concept_agent.taxonomy.get_all_concepts():
        if c.id == req.concept_id:
            mastery_value = concept_agent._get_mastery(c.id).value
            break

    return {
        "success": True,
        "new_mastery": mastery_value,
        "progress": progress_summary,
    }


class AnalyzeDiagramRequest(BaseModel):
    image_data: str
    concept_id: str
    session_id: str = "default"


@router.get("/learning-path/{student_id}")
async def get_learning_path(
    student_id: str,
    diagnostic_agent: DiagnosticIntelligenceAgent = Depends(get_diagnostic_agent),
    curriculum_agent: CurriculumArchitectAgent = Depends(get_curriculum_agent),
):
    """
    Returns a personalized learning path graph structure suitable for rendering in React Flow,
    enriched with neuro-symbolic teaching modalities from the Curriculum Architect.
    """
    try:
        diagnosis = await diagnostic_agent.continuous_diagnosis(student_id)
        curriculum = curriculum_agent.generate_dynamic_curriculum(student_id, diagnosis)
        return curriculum
    except Exception as e:
        logger.error(f"Error generating learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/diagnosis/{student_id}")
async def get_diagnosis(
    student_id: str,
    diagnostic_agent: DiagnosticIntelligenceAgent = Depends(get_diagnostic_agent),
):
    """
    Returns a deep multi-dimensional neuro-symbolic learning profile and mastery predictions.
    """
    try:
        diagnosis = await diagnostic_agent.continuous_diagnosis(student_id)
        return diagnosis
    except Exception as e:
        logger.error(f"Error generating diagnosis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explainable-ai")
async def get_explainable_ai(
    session_id: str = "default",
    meta_agent = Depends(get_meta_agent)
):
    return {
        "decisions": meta_agent.get_session_decisions(session_id)
    }


@router.get("/emotional-analytics")
async def get_emotional_analytics(
    session_id: str = "default",
    emotional_tracker = Depends(get_emotional_tracker)
):
    return await emotional_tracker.analyze_session(session_id)


@router.post("/analyze-diagram")
async def analyze_diagram(
    req: AnalyzeDiagramRequest,
    llm: LLMInterface = Depends(get_llm),
    concept_agent: ConceptGraphAgent = Depends(get_concept_agent),
    emotional_tracker = Depends(get_emotional_tracker)
):
    emotional_tracker.record_retry(req.session_id)
    
    concept = concept_agent.taxonomy.get_concept(req.concept_id)
    concept_name = concept.name if concept else req.concept_id

    fallback_response = {
        "is_correct": False,
        "misconceptions_detected": ["Unable to analyze diagram content dynamically."],
        "feedback": "Your diagram shows the nodes and connections. Make sure to double-check that left children are strictly smaller than parent keys, and check the balance factor rule.",
        "annotations": "Overall structure check."
    }

    if not PIL_AVAILABLE or not llm.available or not req.image_data:
        return fallback_response

    try:
        image_data = req.image_data
        if "," in image_data:
            image_data = image_data.split(",")[1]
        img_bytes = base64.b64decode(image_data)
        img = Image.open(BytesIO(img_bytes))

        prompt = f"""You are an expert Data Structures Tutor. A student has submitted an image of their drawing for the concept "{concept_name}".
        Analyze this image to verify if it correctly depicts the tree data structure and the rules for this concept.
        
        Provide the response in EXACT JSON format with no markdown blocks:
        {{
          "is_correct": true/false,
          "misconceptions_detected": [
            "Specific rule violations (e.g. key ordering violation, recoloring error, balance factor off by 2, etc.)"
          ],
          "feedback": "Encouraging, Socratic feedback explaining what they did well and guiding them on how to correct any issues.",
          "annotations": "Brief description of the problematic nodes or links (e.g. 'Node 25 and its child 30 violate BST order property')."
        }}
        """
        response = llm._model.generate_content([prompt, img])
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(text)
        
        if result.get("is_correct", False):
            concept_agent.record_success(req.concept_id)
        else:
            concept_agent.record_mistake(req.concept_id)

        return result
    except Exception as e:
        logger.warning("Diagram analysis failed: %s", e)
        return fallback_response


@router.websocket("/ws/{session_id}")
async def tutor_websocket(
    websocket: WebSocket,
    session_id: str,
    llm: LLMInterface = Depends(get_llm),
    concept_agent: ConceptGraphAgent = Depends(get_concept_agent),
    emotional_tracker = Depends(get_emotional_tracker),
    meta_agent = Depends(get_meta_agent)
):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "student_message")
            concept_id = data.get("concept_id", "general")
            content = data.get("content", "").strip()

            if not content:
                continue

            session_data = emotional_tracker._get_session_data(session_id)
            history = session_data["messages"]

            if msg_type == "hint_request":
                # Record hint usage
                emotional_tracker.record_hint(session_id)
                emotional_state = await emotional_tracker.analyze_session(session_id)
                
                prompt = f"The student is working on concept '{concept_id}' and requested a hint. Provide a subtle, Socratic hint to help them think without giving the answer. Keep it to 1-2 sentences."
                if llm.available:
                    try:
                        res = llm._model.generate_content(prompt)
                        hint_text = res.text.strip()
                    except Exception:
                        hint_text = "What is the key rule or invariant you are trying to preserve here?"
                else:
                    hint_text = "What is the key rule or invariant you are trying to preserve here?"

                emotional_tracker.record_message(session_id, "tutor", hint_text)
                await websocket.send_json({
                    "type": "tutor_hint",
                    "content": hint_text,
                    "emotional_state": emotional_state
                })
            else:
                # Record user message
                emotional_tracker.record_message(session_id, "user", content)
                emotional_state = await emotional_tracker.analyze_session(session_id)
                
                # Decide strategy
                decision = await meta_agent.decide_strategy(session_id, concept_id, emotional_state)
                strategy = decision["strategy"]
                reason = decision["reason"]

                # Generate reply
                reply_dict = await meta_agent.generate_response(session_id, concept_id, content, history, strategy)
                response_text = reply_dict.get("response", "")
                repaired = reply_dict.get("repaired", False)
                widget = reply_dict.get("widget", None)

                emotional_tracker.record_message(session_id, "tutor", response_text)

                if repaired and concept_id:
                    for _ in range(3):
                        concept_agent.record_success(concept_id)

                # Get the updated mastery
                new_mastery = concept_agent._get_mastery(concept_id).value if concept_id else 0.5

                await websocket.send_json({
                    "type": "tutor_message",
                    "content": response_text,
                    "emotional_state": emotional_state,
                    "pedagogy_strategy": strategy,
                    "pedagogy_reason": reason,
                    "repaired": repaired,
                    "new_mastery": new_mastery,
                    "widget": widget
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket session {session_id} disconnected")
    except Exception as e:
        logger.warning(f"Error in tutor WebSocket: {e}")


