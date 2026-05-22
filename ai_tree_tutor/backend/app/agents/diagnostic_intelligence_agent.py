from typing import Dict, List, Any
import time

from app.llm.base_llm import LLMInterface
from app.agents.base_agent import BaseAgent
from app.agents.concept_graph_agent import ConceptGraphAgent
from app.agents.emotional_tracker import EmotionalStateTracker

class DiagnosticIntelligenceAgent(BaseAgent):
    """
    Agent 1: Continuous assessment & prediction engine.
    Constantly monitors student understanding, predicts mastery trajectories,
    and constructs a multi-dimensional neuro-symbolic profile.
    """
    def __init__(self, llm: LLMInterface, concept_agent: ConceptGraphAgent = None, emotional_tracker: EmotionalStateTracker = None):
        self.llm = llm
        self.concept_agent = concept_agent
        self.emotional_tracker = emotional_tracker

    async def process(self, ctx) -> 'AgentContext':
        # Default pipeline method
        return ctx

    async def continuous_diagnosis(self, student_id: str) -> Dict[str, Any]:
        """
        Gathers multi-source data and predicts future mastery.
        Returns a rich multi-dimensional concept graph.
        """
        # 1. Gather real student data
        data_sources = await self._gather_student_data(student_id)
        
        # 2. Neural predictor component (predicting future mastery based on real performance)
        mastery_prediction = self._predict_trajectory(data_sources, time_horizon="7_days")
        
        # 3. Symbolic reasoning: Use LLM to diagnose root causes
        symbolic_analysis = self._run_symbolic_diagnosis(data_sources)
        
        # 4. Build the dynamic concept graph
        concept_graph = self._build_dynamic_graph(
            neural_predictions=mastery_prediction,
            symbolic_analysis=symbolic_analysis,
            real_time_performance=data_sources
        )
        
        return {
            'student_id': student_id,
            'current_state': concept_graph,
            'predicted_mastery': mastery_prediction,
            'intervention_needed': self._detect_intervention_points(concept_graph),
            'optimal_next_activity': self._recommend_next_step(concept_graph)
        }

    async def _gather_student_data(self, student_id: str) -> Dict[str, Any]:
        """Aggregates real student metrics from active tracking agents."""
        # 1. Fetch real emotional and session metrics from EmotionalStateTracker
        sentiment = "neutral"
        cognitive_load = "medium"
        engagement_level = 75
        hints_used = 0
        retries = 0
        avg_response_time = 0.0
        session_len = 10
        
        if self.emotional_tracker:
            emotion = await self.emotional_tracker.analyze_session(student_id)
            sentiment = emotion.get("sentiment", "neutral")
            cognitive_load = emotion.get("cognitive_load", "medium")
            engagement_level = emotion.get("engagement_level", 75)
            hints_used = emotion.get("hints_used", 0)
            retries = emotion.get("retries", 0)
            avg_response_time = emotion.get("avg_response_time", 0.0)
            
            sess_data = self.emotional_tracker._sessions.get(student_id, {})
            last_msg_t = sess_data.get("last_message_time", 0.0)
            if last_msg_t > 0:
                session_len = max(1, int((time.time() - last_msg_t) / 60) + 10)

        # 2. Fetch real performance metrics from ConceptGraphAgent
        avg_mastery = 0.5
        total_mistakes = 0
        total_attempts = 0
        
        if self.concept_agent:
            summary = self.concept_agent.get_progress_summary()
            avg_mastery = summary.get("average_mastery", 0.5)
            total_mistakes = sum(m.mistakes for m in self.concept_agent.mastery.values())
            total_attempts = sum(m.attempts for m in self.concept_agent.mastery.values())
            
        score_percentage = avg_mastery * 100.0
        
        return {
            'quiz_history': {
                'score': round(score_percentage, 1),
                'recent_mistakes': total_mistakes,
                'total_attempts': total_attempts
            },
            'chat_interactions': {
                'sentiment': sentiment,
                'cognitive_load': cognitive_load,
                'engagement_level': engagement_level,
                'hints_used': hints_used,
                'retries': retries,
                'avg_response_time': avg_response_time
            },
            'time_patterns': {
                'peak_focus_time': 'Active Session',
                'current_session_length': session_len
            },
            'peer_comparisons': {
                'percentile': min(99, max(5, int(avg_mastery * 100)))
            },
        }

    def _predict_trajectory(self, student_data: Dict, time_horizon: str) -> Dict[str, Any]:
        """Predicts future mastery using actual student performance trends."""
        current_mastery = student_data['quiz_history']['score'] / 100.0
        sentiment = student_data['chat_interactions']['sentiment']
        cognitive_load = student_data['chat_interactions']['cognitive_load']
        
        # Calculate learning growth rate based on emotional valence & load
        growth = 0.08
        if sentiment in ['excited', 'confident']:
            growth += 0.06
        elif sentiment in ['frustrated', 'stressed']:
            growth -= 0.12
        elif sentiment in ['confused', 'bored']:
            growth -= 0.04
            
        if cognitive_load == 'overload':
            growth -= 0.06
        elif cognitive_load == 'high':
            growth -= 0.02
        elif cognitive_load == 'low':
            growth += 0.02
            
        total_attempts = student_data['quiz_history'].get('total_attempts', 0)
        confidence = min(0.95, max(0.3, 0.4 + 0.05 * total_attempts))
        
        return {
            'time_horizon': time_horizon,
            'predicted_mastery': min(1.0, max(0.0, round(current_mastery + growth, 2))),
            'confidence': round(confidence, 2)
        }

    def _run_symbolic_diagnosis(self, data_sources: Dict) -> Dict[str, Any]:
        """Uses the LLM to generate deep psychological/cognitive insights."""
        prompt = f"""
        Analyze this student's learning profile:
        {data_sources}
        
        Identify:
        1. Hidden misconceptions
        2. Learning style preferences
        3. Emotional patterns affecting learning
        
        Return exactly JSON format:
        {{
            "hidden_misconceptions": ["string"],
            "learning_style": "string",
            "emotional_state": "string"
        }}
        """
        if not self.llm.available:
             return {
                 "hidden_misconceptions": ["Requires conceptual reinforcement"],
                 "learning_style": "Visual & Interactive",
                 "emotional_state": data_sources['chat_interactions']['sentiment']
             }
             
        try:
            result = self.llm._query(prompt)
            if result and isinstance(result, dict) and "hidden_misconceptions" in result:
                return result
        except Exception:
            pass
            
        return {
             "hidden_misconceptions": ["Requires conceptual reinforcement"],
             "learning_style": "Visual & Interactive",
             "emotional_state": data_sources['chat_interactions']['sentiment']
        }

    def _build_dynamic_graph(self, neural_predictions: Dict, symbolic_analysis: Dict, real_time_performance: Dict) -> Dict[str, Any]:
        """Constructs a fully dynamic multi-dimensional concept graph."""
        nodes = []
        all_concepts = []
        
        if self.concept_agent:
            all_concepts = self.concept_agent.taxonomy.get_all_concepts()
            
        current_overall = real_time_performance['quiz_history']['score'] / 100.0
        predicted_overall = neural_predictions['predicted_mastery']
        growth = predicted_overall - current_overall
        
        # Populate dynamic nodes using all concepts in the taxonomy
        for concept in all_concepts:
            m = self.concept_agent._get_mastery(concept.id)
            blockers = []
            
            # Check for prerequisite gaps
            for prereq_id in concept.prerequisites:
                prereq_m = self.concept_agent._get_mastery(prereq_id)
                if prereq_m.value < 0.5:
                    prereq_concept = self.concept_agent.taxonomy.get_concept(prereq_id)
                    prereq_name = prereq_concept.name if prereq_concept else prereq_id
                    blockers.append(f"Prerequisite '{prereq_name}' is not yet mastered.")
            
            # Check for misconceptions
            if m.misconception_count >= 1:
                blockers.append(f"Active misconception: {concept.false_belief}")
                
            predicted_concept_mastery = min(1.0, max(0.0, m.value + growth))
            
            nodes.append({
                'concept': concept.id,
                'concept_name': concept.name,
                'mastery': round(m.value, 2),
                'predicted_mastery': round(predicted_concept_mastery, 2),
                'confidence': round(m.confidence, 2),
                'blockers': blockers or symbolic_analysis.get('hidden_misconceptions', [])
            })
            
        # If taxonomy was empty, fallback gracefully
        if not nodes:
            nodes.append({
                'concept': 'avl_balance_factor',
                'concept_name': 'AVL Balance Factor',
                'mastery': round(real_time_performance['quiz_history']['score'] / 100.0, 2),
                'predicted_mastery': round(neural_predictions['predicted_mastery'], 2),
                'confidence': round(neural_predictions['confidence'], 2),
                'blockers': symbolic_analysis.get('hidden_misconceptions', [])
            })

        # Calculate dynamic skill scores based on concept categories
        core_scores = []
        op_scores = []
        for concept in all_concepts:
            val = self.concept_agent._get_mastery(concept.id).value
            if concept.category.value in ("core", "prerequisite"):
                core_scores.append(val)
            elif concept.category.value == "operation":
                op_scores.append(val)
                
        avg_core = sum(core_scores) / len(core_scores) if core_scores else 0.5
        avg_op = sum(op_scores) / len(op_scores) if op_scores else 0.5
        
        total_mistakes = real_time_performance['quiz_history']['recent_mistakes']
        total_attempts = real_time_performance['quiz_history']['total_attempts']
        problem_solving_factor = 1.0 - (total_mistakes / max(1, total_attempts))
        problem_solving = min(1.0, max(0.2, (avg_op + problem_solving_factor) / 2.0))

        # Dynamic metacognitive scores
        hints = real_time_performance['chat_interactions']['hints_used']
        retries = real_time_performance['chat_interactions']['retries']
        self_awareness = min(1.0, max(0.2, 0.85 - (hints * 0.08) - (retries * 0.04)))
        
        avg_resp = real_time_performance['chat_interactions'].get('avg_response_time', 15.0)
        self_regulation = min(1.0, max(0.2, 0.9 - (total_mistakes * 0.06) - (max(0.0, avg_resp - 30.0) * 0.003)))

        # Dynamic emotional confidence & motivation
        sentiment = real_time_performance['chat_interactions']['sentiment']
        cognitive_load = real_time_performance['chat_interactions']['cognitive_load']
        engagement_level = real_time_performance['chat_interactions']['engagement_level']
        
        base_conf = 0.55
        if sentiment in ['excited', 'confident']:
            base_conf += 0.15
        elif sentiment in ['frustrated']:
            base_conf -= 0.20
            
        if cognitive_load == 'overload':
            base_conf -= 0.15
            
        confidence_factor = min(1.0, max(0.1, base_conf))
        motivation_factor = min(1.0, max(0.1, engagement_level / 100.0))

        return {
            'knowledge_dimension': {
                'nodes': nodes
            },
            'skill_dimension': {
                'problem_solving': round(problem_solving, 2),
                'conceptual_understanding': round(avg_core, 2),
                'application': round(avg_op, 2),
            },
            'meta_cognitive_dimension': {
                'self_awareness': round(self_awareness, 2),
                'self_regulation': round(self_regulation, 2)
            },
            'emotional_dimension': {
                'state': symbolic_analysis.get('emotional_state', 'neutral'),
                'confidence': round(confidence_factor, 2),
                'motivation': round(motivation_factor, 2)
            }
        }

    def _detect_intervention_points(self, concept_graph: Dict) -> List[str]:
        """Identifies if immediate action is needed by examining all concepts."""
        points = []
        if concept_graph['emotional_dimension']['state'].lower() in ['frustrated', 'stressed', 'overwhelmed', 'confused']:
            points.append("Emotional support needed")
            
        # Check if any concept has a predicted mastery below 50%
        predicted_failures = [
            node['concept_name'] for node in concept_graph['knowledge_dimension']['nodes']
            if node['predicted_mastery'] < 0.5
        ]
        if predicted_failures:
            points.append(f"Predicted concept failure on: {', '.join(predicted_failures[:2])}")
            
        return points

    def _recommend_next_step(self, concept_graph: Dict) -> str:
        """Determines the optimal next step based on all dynamic concept nodes."""
        interventions = self._detect_intervention_points(concept_graph)
        if "Emotional support needed" in interventions:
            return "Take a 5-minute break or request a simple analogy in the tutor chat."
            
        # Find weakest active concept
        weakest_node = None
        for node in concept_graph['knowledge_dimension']['nodes']:
            if weakest_node is None or node['mastery'] < weakest_node['mastery']:
                weakest_node = node
                
        if weakest_node and weakest_node['mastery'] < 0.5:
            return f"Start a Concept Repair session for '{weakest_node['concept_name']}'."
            
        return "You have excellent conceptual health! Keep taking quizzes to challenge yourself."
