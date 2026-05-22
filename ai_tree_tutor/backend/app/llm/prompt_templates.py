from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError):
        return str(obj)


def _truncate(text: str, max_chars: int = 300) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


GROUNDING_RULES = """GROUNDING RULES (you MUST follow ALL):
1. The symbolic validator output is GROUND TRUTH. Never contradict it.
2. If you are unsure about a specific tree property, say "I recommend reviewing the textbook section on this topic" — do NOT fabricate rules.
3. Never invent tree states, node values, or operation outcomes. Only reference facts provided in this prompt.
4. Limit explanations to 4-6 sentences maximum unless otherwise specified.
5. Every claim must be directly derivable from the symbolic validator output or established CS textbook knowledge (CLRS, Sedgewick).
6. If asked about a concept you are uncertain of, state the uncertainty and suggest review material — do not guess."""

SYSTEM_PROMPT = f"""You are an expert Data Structures professor and Doubts Resolver.

Your role: Diagnose student misconceptions and teach tree data structures (AVL, Red-Black, Heap, B-Tree, B+ Tree, Segment Tree).

Teaching philosophy:
  - Provide direct, simple, and clear explanations. Always give the answer and explain it simply.
  - Explain WHY before WHAT: always start with the conceptual reason, then the mechanical step.
  - Address the false belief directly: name the misconception and explain why it is wrong.
  - Connect to prerequisites: show how concepts build on each other.
  - Use concise, precise language — no fluff, no tangents.

{GROUNDING_RULES}"""


class PromptTemplates:

    @staticmethod
    def system() -> str:
        return SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # 1. Diagnosis prompt
    # ------------------------------------------------------------------

    def diagnosis(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        misconception_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        adaptive = ""
        if misconception_context:
            adaptive = f"""
ADAPTIVE CONTEXT (student's learning history):
  - Previously diagnosed pattern: {misconception_context.get('pattern', 'first occurrence')}
  - Known false belief: {misconception_context.get('false_belief', 'unknown')}
  - Prerequisite gaps: {misconception_context.get('prerequisite_gaps', [])}
  - Conceptual difficulty: {misconception_context.get('difficulty', 'medium')}

Use this context to tailor your diagnosis — if the student has a known false belief, address it directly."""

        return f"""{GROUNDING_RULES}

You are diagnosing a student's tree data structure misconception.

CONTEXT:
Tree type: {tree_type}
Operation: {operation}
Symbolic validator detected: {violation.get('type', 'unknown')}
Violation details: {_safe_json(violation)}
{adaptive}

DIAGNOSE THE MISCONCEPTION. Respond in EXACT JSON format:
{{
  "misconception": "one clear sentence naming the core misunderstanding",
  "root_cause": "one sentence explaining why this violation occurred conceptually",
  "false_belief_addressed": "the specific wrong idea the student holds that causes this — name it directly",
  "concept_area": "must be one of: avl_balance_factor | avl_rotations | bst_property | tree_height | rb_coloring | rb_black_height | heap_property | heapify | btree_split | btree_merge | segment_build | segment_query | lazy_propagation | pointer_manipulation | complete_tree | recursion",
  "severity": "must be one of: low | medium | high",
  "why_happened": "one sentence explaining the conceptual error, not just the mechanical mistake",
  "related_concepts": ["list of 2-4 concept IDs this connects to"]
}}

CONSTRAINTS:
  - "misconception" must be UNDER 20 words
  - "root_cause" must be UNDER 15 words
  - "why_happened" must explain the THINKING error, not the coding error
  - If uncertain about any specific claim, state it in "misconception" rather than guessing"""

    # ------------------------------------------------------------------
    # 2. Socratic teaching prompt
    # ------------------------------------------------------------------

    def teaching(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        misconception: str,
        false_belief: Optional[str] = None,
        prerequisite_gaps: Optional[List[str]] = None,
        student_history: Optional[List[Dict]] = None,
    ) -> str:
        false_belief_block = ""
        if false_belief:
            false_belief_block = f"""\nThe student likely holds this FALSE BELIEF: "{false_belief}"
Address this false belief directly — explain WHY it is wrong."""

        prereq_block = ""
        if prerequisite_gaps:
            prereq_block = f"""\nThe student may be missing prerequisite concepts: {', '.join(prerequisite_gaps[:2])}
If the explanation requires these, briefly revisit the prerequisite first."""

        return f"""{GROUNDING_RULES}

You are teaching a student about {tree_type} after they made an error.

CONTEXT:
Operation: {operation}
Symbolic violation: {violation.get('type', 'unknown')} — {violation.get('message', '')}
Diagnosed misconception: "{misconception}"{false_belief_block}{prereq_block}

DIRECT TEACHING METHOD — follow this structure:
  1. Start with a direct, simple explanation of what went wrong
  2. Then name the false belief and WHY it is wrong
  3. Explain WHY the tree property exists (what problem it solves conceptually)
  4. State the correct rule/formula precisely
  5. Walk through the specific violation — WHAT should have happened

Respond in EXACT JSON format:
{{
  "explanation": "4-6 sentences. First sentence: direct explanation. Second sentence: name the false belief and why it is wrong. Third sentence: WHY this property exists. Fourth: the correct rule. Remaining: walk through the violation conceptually.",

  "step_by_step": [
    "Step 1: [conceptual action] — WHY: [reason this step exists, what invariant it maintains]",
    "Step 2: [conceptual action] — WHY: [reason]"
  ],

  "worked_example": {{
    "before": "Tree state BEFORE the operation (use simple notation like [10, 5, 15])",
    "students_approach": "What the student did wrong, in 1-2 sentences",
    "correct_approach": "What should have happened, in 1-2 sentences",
    "after": "Tree state AFTER the correct approach"
  }},

  "why_this_matters": "2-3 sentences on what would go wrong conceptually if this property were ignored (connect to Big-O or correctness)",

  "guiding_question": "A simple statement summarizing the takeaway or a simple question.",

  "follow_up_question": "A simple question the student should answer after reflecting — must start with 'What would happen if' or 'How would'",

  "key_rule": "State the precise mathematical/invariant rule in ONE sentence",

  "common_mistake": "The most common conceptual error students make on this topic, and WHY they make it"
}}

CONSTRAINTS:
  - "explanation" must be EXACTLY 4-6 sentences and directly explain the concept
  - Each "step_by_step" entry must have a WHY clause
  - "why_this_matters" must connect to a REAL consequence
  - Never include code blocks — use plain language
  - If uncertain about a specific claim, replace it with a recommendation to consult CLRS"""

    # ------------------------------------------------------------------
    # 3. Adaptive hint with Socratic progression
    # ------------------------------------------------------------------

    def adaptive_hint(
        self,
        tree_type: str,
        operation: str,
        violation: Dict[str, Any],
        attempt_number: int,
        previous_hints: Optional[List[str]] = None,
        student_ability: str = "medium",
    ) -> str:
        if attempt_number <= 1:
            scaffolding = "minimal"
        elif attempt_number == 2:
            scaffolding = "socratic"
        elif attempt_number == 3:
            scaffolding = "directive"
        else:
            scaffolding = "explanatory"

        previous = ""
        if previous_hints:
            prev_text = "; ".join(previous_hints[-2:])
            previous = f"""\nPrevious hints given (do NOT repeat these): {prev_text}"""

        return f"""{GROUNDING_RULES}

You are providing an adaptive hint to a student working on a {tree_type} problem.

CONTEXT:
Operation: {operation}
Violation: {violation.get('type', 'unknown')}
Student attempt number: {attempt_number}
Scaffolding level: {scaffolding}{previous}
Student ability estimate: {"strong" if attempt_number <= 1 else "struggling" if attempt_number >= 3 else "developing"}

HINT STRATEGY — {scaffolding}:
  - minimal: Name the concept to review and provide a brief direct explanation.
  - socratic: Provide a clear explanation that directly points to the solution.
  - directive: State the rule and explain exactly how to apply it.
  - explanatory: Provide the step-by-step fix with full reasoning.

Respond in EXACT JSON:
{{
  "hint": "The hint text — direct and simple explanation",
  "scaffolding_level": "{scaffolding}",
  "concept_to_review": "concept_id the student should review",
  "guiding_question": "a simple question to verify understanding",
  "rule_reference": "state the precise rule",
  "encouragement": "one short sentence of encouragement",
  "follow_up_question": "a question that checks understanding"
}}

CONSTRAINTS:
  - Provide direct help and explanations at all levels. No more hiding the answer.
  - At explanatory: provide the fix and explain it simply."""

    # ------------------------------------------------------------------
    # 4. Quiz question generation
    # ------------------------------------------------------------------

    def quiz_question(
        self,
        tree_type: str,
        concept: str,
        difficulty: float,
        student_mastery: float = 0.5,
        question_type: str = "reasoning",
        misconception: Optional[str] = None,
    ) -> str:
        difficulty_label = self._difficulty_label(difficulty)
        mastery_context = f"Student mastery of this concept: {student_mastery:.0%}"
        misconception_block = ""
        if misconception:
            misconception_block = f"""\nKNOWN MISCONCEPTION to target: "{misconception}"
Design a distractor option that matches this misconception — so answering incorrectly reveals this specific misunderstanding."""

        type_instructions = {
            "reasoning": "The question must require MULTI-STEP REASONING. The student must combine 2+ concepts to arrive at the answer. Provide a trace or scenario, not a fact recall.",
            "visualization": "The question must present a TREE STATE and ask the student to predict the result of an operation. Use bracket notation like [10, 5, 15] for trees.",
            "misconception_targeted": f"The question must specifically test the misconception '{misconception}'. One distractor must match the false belief exactly. The correct answer must explicitly contradict the false belief. {misconception_block or ''}",
            "conceptual": "The question must ask WHY a property exists or WHAT would go wrong without it. There should be no numeric computation — only conceptual reasoning.",
            "trace": "The question must present a sequence of operations and ask the student to identify the correct intermediate or final tree state.",
        }
        type_note = type_instructions.get(question_type, type_instructions["reasoning"])

        return f"""{GROUNDING_RULES}

You are generating a quiz question for an AI tutoring platform.

CONTEXT:
Tree type: {tree_type}
Concept: {concept}
Difficulty level: {difficulty_label} (numerical: {difficulty:.1f})
Question type: {question_type}
{mastery_context}{misconception_block}

INSTRUCTION: {type_note}

Respond in EXACT JSON:
{{
  "question": "the question text — clear, unambiguous, must require {question_type}",
  "options": ["A", "B", "C", "D"],
  "correct_index": 0,
  "explanation": "why the correct answer is right AND why each distractor is wrong (1-2 sentences each)",
  "concept": "{concept}",
  "difficulty": {difficulty},
  "difficulty_label": "{difficulty_label}",
  "question_type": "{question_type}",
  "misconception_targeted": "{misconception or ''}",
  "reasoning_steps": ["step 1", "step 2", "step 3"]
}}

CONSTRAINTS:
  - "question" must not be answerable by memorisation — require reasoning or visualisation
  - Distractors must be PLAUSIBLE — common student errors, not random wrong answers
  - If difficulty >= 0.5, include at least one distractor that matches a known misconception
  - "explanation" must explain WHY each wrong answer is wrong, not just why the right answer is right
  - Do NOT use the word 'always' or 'never' unless mathematically precise"""

    # ------------------------------------------------------------------
    # 5. Answer evaluation
    # ------------------------------------------------------------------

    def answer_evaluation(
        self,
        question: Dict[str, Any],
        student_answer: str,
        correct_answer: str,
        is_correct: bool,
        student_history: Optional[List[Dict]] = None,
    ) -> str:
        history_block = ""
        if student_history:
            recent = student_history[-5:]
            history_block = f"""\nStudent's recent performance: {_safe_json(recent)}"""

        return f"""{GROUNDING_RULES}

You are evaluating a student's answer in an AI tutoring system.

CONTEXT:
Question: {question.get('question', '')}
Concept: {question.get('concept', 'unknown')}
Question type: {question.get('question_type', 'reasoning')}
Correct answer: {correct_answer}
Student's answer: {student_answer}
Was correct: {is_correct}{history_block}

Respond in EXACT JSON:
{{
  "is_correct": {str(is_correct).lower()},
  "feedback": "2-3 sentences. Provide a direct, simple explanation of the concept. If wrong: explain the conceptual gap and give the correct reasoning.",
  "conceptual_gap": "if wrong: name the specific conceptual misunderstanding revealed by their wrong answer — otherwise empty string",
  "misconception_detected": "a misconception ID or empty string if none detected",
  "socratic_follow_up": "a simple question that probes deeper into the concept",
  "next_difficulty": {question.get('difficulty', 0.5)},
  "encouragement": "one sentence of specific, genuine encouragement"
}}

CONSTRAINTS:
  - Focus feedback on CONCEPT, not on the specific numeric answer
  - Give a direct explanation instead of making them guess
  - Never shame the student — always frame gaps as "common misunderstanding that many students have"
  - next_difficulty: increase by 0.1-0.2 if correct, decrease by 0.1-0.2 if wrong"""

    # ------------------------------------------------------------------
    # 6. Complexity explanation
    # ------------------------------------------------------------------

    def complexity(self, tree_type: str, operation: str, student_mastery: float = 0.5) -> str:
        depth = "detailed_intuition" if student_mastery >= 0.5 else "intuitive"
        return f"""{GROUNDING_RULES}

Explain the time/space complexity of '{operation}' on a {tree_type}.

Student mastery level: {student_mastery:.0%}
Explanation depth: {depth}

{depth} explanation:
  - intuitive: Focus on INTUITION. Use analogies. Avoid formal proof.
  - detailed_intuition: Explain WHY each case has its complexity. Show how the tree structure determines the bound.

Respond in EXACT JSON:
{{
  "operation": "{operation}",
  "tree_type": "{tree_type}",
  "time_complexity": {{
    "best_case": "O(?) with explanation (1-2 words)",
    "average_case": "O(?) with explanation",
    "worst_case": "O(?) with explanation"
  }},
  "space_complexity": "O(?) with 1-2 word explanation",
  "intuition": "1-2 sentences giving intuition for WHY — the 'so what' that connects the O() notation to tree structure",
  "comparison": "one sentence comparing this operation's complexity to the same operation on other tree types"
}}

CONSTRAINTS:
  - "intuition" must reference the actual tree structure (height, balance, node degrees)
  - If depth is 'intuitive', omit formal proof entirely
  - Each O() notation must include a brief parenthetical explanation like "O(log n) — tree height" """

    # ------------------------------------------------------------------
    # 7. System prompt for quiz generation mode
    # ------------------------------------------------------------------

    @staticmethod
    def quiz_system_prompt() -> str:
        return f"""{SYSTEM_PROMPT}

You are now in QUIZ GENERATION MODE:
  - Generate questions that test CONCEPTUAL UNDERSTANDING, not memorisation.
  - Each distractor should represent a real, documented student misconception.
  - For any visualization question, provide the tree state in clear notation.
  - Ensure questions are self-contained — the student has no external references.
  - Difficulty must be calibrated so the student has ~60-70% chance of answering correctly for optimal learning."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _difficulty_label(difficulty: float) -> str:
        if difficulty < 0.3:
            return "easy"
        if difficulty < 0.5:
            return "medium_easy"
        if difficulty < 0.7:
            return "medium"
        if difficulty < 0.9:
            return "hard"
        return "expert"

    @staticmethod
    def _extract_concept_id(concept: str) -> str:
        mapping = {
            "balance factor": "avl_balance_factor",
            "avl rotations": "avl_rotation_cases",
            "bst property": "bst_property",
            "tree height": "tree_height",
            "red black coloring": "rb_coloring",
            "rb properties": "rb_properties",
            "heap property": "heap_property",
            "heapify": "heapify",
            "b tree splitting": "btree_node_split",
            "segment tree queries": "seg_range_query",
            "lazy propagation": "seg_lazy_push",
            "pointer manipulation": "pointer_manipulation",
            "recursive thinking": "recursion",
        }
        return mapping.get(concept.lower().strip(), concept.lower().replace(" ", "_"))
