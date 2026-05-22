from typing import Dict, List, Any

from app.llm.base_llm import LLMInterface
from app.agents.base_agent import BaseAgent
from app.agents.concept_graph_agent import ConceptGraphAgent
from app.concept_graph.learning_path import LearningPathGenerator

class CurriculumArchitectAgent(BaseAgent):
    """
    Agent 5: Creates personalized, adaptive learning paths.
    Wraps the topological LearningPathGenerator and uses the LLM to 
    design modalities, pacing, and assessment strategies.
    """
    def __init__(self, llm: LLMInterface, concept_agent: ConceptGraphAgent):
        self.llm = llm
        self.concept_agent = concept_agent
        self.path_generator = LearningPathGenerator(concept_agent)

    async def process(self, ctx) -> 'AgentContext':
        return ctx

    def generate_dynamic_curriculum(self, student_id: str, student_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete adaptive curriculum combining topological graph and neuro-symbolic design.
        """
        # 1. Get raw topological sequence
        raw_path = self.path_generator.generate_path(student_id)
        
        # 2. Extract concepts for the prompt
        sequence = [node.get('concept_id') for node in raw_path.get("sequence", [])]
        
        # 3. Ask LLM to enrich the curriculum
        enriched = self._enrich_curriculum_with_llm(student_profile, sequence)
        
        return {
            'student_id': student_id,
            'learning_path': raw_path,  # Fallback/structural data
            'enriched_curriculum': enriched
        }

    def _enrich_curriculum_with_llm(self, profile: Dict, sequence: List[str]) -> Dict[str, Any]:
        """Uses LLM to design teaching modalities, pacing, and adaptation triggers."""
        prompt = f"""
        Design a complete personalized curriculum:
        
        Student Profile (from Diagnostic Agent): {profile}
        Topological Sequence to Learn: {sequence}
        
        Return EXACT JSON format:
        {{
            "teaching_modalities": {{
                "visual_percentage": 0,
                "interactive_percentage": 0,
                "peer_percentage": 0
            }},
            "assessment_strategy": ["formative_checkpoints", "summative_projects"],
            "adaptation_triggers": ["slow_down_if_frustrated", "skip_if_mastered"]
        }}
        """
        if not self.llm.available:
            return self._fallback_curriculum(profile)
            
        try:
            result = self.llm._query(prompt)
            if result and "teaching_modalities" in result:
                return result
        except Exception:
            pass
            
        return self._fallback_curriculum(profile)
        
    def _fallback_curriculum(self, profile: Dict) -> Dict[str, Any]:
        """
        Dynamically calculates teaching modalities, assessment strategies,
        and adaptation triggers based on real student performance and emotional tracking.
        """
        current_state = profile.get("current_state", {})
        emotional = current_state.get("emotional_dimension", {})
        meta_cognitive = current_state.get("meta_cognitive_dimension", {})
        
        sentiment = emotional.get("state", "neutral").lower()
        confidence = emotional.get("confidence", 0.5)
        
        # Calculate teaching modalities based on student state
        visual = 40.0
        interactive = 40.0
        peer = 20.0
        
        if sentiment in ['frustrated', 'stressed', 'overwhelmed']:
            interactive += 15.0
            visual -= 5.0
            peer -= 10.0
        elif sentiment in ['bored', 'unmotivated']:
            interactive += 20.0
            visual -= 10.0
            peer -= 10.0
        elif sentiment in ['excited', 'confident']:
            peer += 15.0
            interactive -= 10.0
            visual -= 5.0
            
        if confidence < 0.4:
            visual += 10.0
            interactive += 5.0
            peer -= 15.0
            
        tot = visual + interactive + peer
        visual_p = int(round((visual / tot) * 100))
        interactive_p = int(round((interactive / tot) * 100))
        peer_p = 100 - visual_p - interactive_p
        
        self_regulation = meta_cognitive.get("self_regulation", 0.5)
        self_awareness = meta_cognitive.get("self_awareness", 0.5)
        
        assessment_strategy = []
        if self_regulation < 0.5:
            assessment_strategy.append("Frequent guided formative checkpoints with immediate step-by-step hints")
        else:
            assessment_strategy.append("Open-ended application challenges with summative self-assessment")
            
        if self_awareness < 0.5:
            assessment_strategy.append("Self-reflection micro-prompts asking the student to rate their confidence before submitting answers")
        else:
            assessment_strategy.append("Automated diagnostic checks after completing major topic groups")
            
        adaptation_triggers = []
        if confidence < 0.5:
            adaptation_triggers.append("Decrease task difficulty and inject high-motivation reinforcement blocks if confidence is low")
        else:
            adaptation_triggers.append("Inject advanced concept application tasks and challenge problems")
            
        if sentiment in ['frustrated', 'stressed']:
            adaptation_triggers.append("Propose an immediate cognitive pause or Socratic breakdown of the problem")
        elif sentiment in ['bored']:
            adaptation_triggers.append("Trigger gamified quiz mode or fast-track through mastered prerequisites")
            
        return {
            "teaching_modalities": {
                "visual_percentage": visual_p,
                "interactive_percentage": interactive_p,
                "peer_percentage": peer_p
            },
            "assessment_strategy": assessment_strategy,
            "adaptation_triggers": adaptation_triggers
        }
