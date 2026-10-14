from typing import Dict, List, Optional
import random

from app.llm.base_llm import LLMInterface
from app.agents.base_agent import BaseAgent

class AdaptiveTeachingAgent(BaseAgent):
    """
    Adaptive Teaching Agent that selects and executes dynamic teaching strategies
    based on the student's conversation.
    """
    def __init__(self, llm: LLMInterface):
        self.llm = llm
        
        # We start with basic modes: socratic dialogue and visual explanation.
        self.teaching_modes = {
            'socratic': self.socratic_dialogue,
            'visual': self.visual_explanation
        }

    async def process(self, ctx) -> 'AgentContext':
        # Default agent pipeline method; currently unused by teach_dynamically
        return ctx

    def teach_dynamically(self, history_str: str, message: str, concept_id: str) -> Dict:
        """
        Determine the best strategy and teach dynamically.
        Returns a dictionary matching the tutor_chat expected output:
        {
          "response": str,
          "repaired": bool,
          "widget": dict or None
        }
        """
        # MVP Strategy Selection: Determine if we should send a visual based on keywords
        # or if we should just use Socratic dialogue.
        visual_triggers = ['draw', 'show', 'visualize', 'diagram', 'picture', 'graph', 'tree', 'example']
        strategy = 'socratic'
        
        message_lower = message.lower()
        if any(trigger in message_lower for trigger in visual_triggers):
            strategy = 'visual'
        # Also random chance to inject a visual to keep engagement high
        elif random.random() < 0.2:
            strategy = 'visual'
            
        try:
            return self.teaching_modes[strategy](history_str, message, concept_id)
        except Exception as e:
            # Fallback to socratic if anything fails
            return self.socratic_dialogue(history_str, message, concept_id)

    def socratic_dialogue(self, history_str: str, message: str, concept_id: str) -> Dict:
        """Guide discovery through Socratic questioning."""
        prompt = f"""You are an Expert Data Structures AI Assistant.
        Respond to the student's question or message directly and comprehensively.
        
        GROUNDING RULES:
        1. Answer the student's questions directly, clearly, and completely.
        2. Provide clear explanations, code examples (if helpful), and direct solutions when asked.
        3. Be as helpful and informative as a standard AI assistant (like ChatGPT).
        4. You do not need to ask guiding questions. Just answer the user's doubt.
        
        CONTEXT:
        Target Concept: {concept_id or "General Tree Structures"}
        
        RECENT CHAT HISTORY:
        {history_str}
        Student's new message: "{message}"
        
        Provide your response in EXACT JSON format:
        {{
          "response": "Your Socratic conversational response here.",
          "repaired": false,
          "widget": null
        }}
        
        CONSTRAINTS:
        - Return ONLY valid JSON, do not wrap in markdown code fences.
        - CRITICAL: Ensure all strings properly escape double quotes (\") and newlines (\\n). DO NOT output raw unescaped newlines inside JSON string values.
        - "repaired" should be true ONLY IF the student has explicitly demonstrated full mastery and understanding of the concept in their message. Otherwise false.
        """
        if not self.llm.available:
            return {"response": "The Socratic API is currently unavailable.", "repaired": False, "widget": None}
            
        result = self.llm._query(prompt)
        if result and "response" in result:
            # Ensure keys exist
            if "repaired" not in result:
                result["repaired"] = False
            if "widget" not in result:
                result["widget"] = None
            return result
        return {"response": "Could you elaborate on that?", "repaired": False, "widget": None}

    def visual_explanation(self, history_str: str, message: str, concept_id: str) -> Dict:
        """Multi-layered visual teaching using SVG/HTML widgets."""
        prompt = f"""You are an Adaptive Visual Data Structures Tutor.
        The student needs help with the concept: {concept_id or "General Tree Structures"}
        
        RECENT CHAT HISTORY:
        {history_str}
        Student's new message: "{message}"
        
        Provide your response in EXACT JSON format:
        {{
          "response": "A concise, engaging response that introduces the visual diagram you generated.",
          "repaired": false,
          "widget": {{
             "type": "html",
             "content": "Provide self-contained, valid HTML containing an SVG diagram or styled div blocks illustrating the concept. Use vibrant colors, smooth styles, and modern design. Keep it compact."
          }}
        }}
        
        CONSTRAINTS:
        - Return ONLY valid JSON, do not wrap in markdown code fences.
        - "repaired" should be true ONLY IF the student has explicitly demonstrated full mastery. Otherwise false.
        - The widget content MUST be valid HTML. Do not use markdown inside the widget content.
        - Ensure SVG tags are properly closed.
        """
        if not self.llm.available:
            return {"response": "Visual generation is currently unavailable.", "repaired": False, "widget": None}
            
        result = self.llm._query(prompt)
        if result and "response" in result:
            if "repaired" not in result:
                result["repaired"] = False
            return result
        return self.socratic_dialogue(history_str, message, concept_id)
