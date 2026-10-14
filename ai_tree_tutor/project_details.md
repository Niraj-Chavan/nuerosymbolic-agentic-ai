# AI Tree Tutor: Comprehensive Architecture & Workflows

## 1. System Overview
**AI Tree Tutor** is an advanced, neuro-symbolic tutoring system designed to teach complex tree data structures. Instead of presenting static lessons, the system learns about the student. It models the student's brain using a hierarchical **Concept Knowledge Graph** and uses **Agentic AI** (powered by Google Gemini) to dynamically adjust the difficulty, provide direct help, and construct personalized learning paths.

---

## 2. The Core Agentic Pipeline

The backend relies on specialized "Agents" that each handle a specific phase of the learning loop. 

### Tree Execution Agent (`tree_execution_agent.py`)
- **What it does:** Runs the deterministic algorithms for tree operations (AVL, Red-Black, Heaps, B-Trees, etc.).
- **How it works:** When a student asks to insert a node, this agent actually performs the standard algorithm in Python. It records the state of the tree at every microscopic step (e.g., comparing keys, identifying a rotation case, updating a height). These steps are passed to the frontend to animate the process.

### Symbolic Validation Agent (`validation_agent.py`)
- **What it does:** Acts as a strict mathematical rule-checker.
- **How it works:** After an operation is performed, it mathematically verifies if the resulting tree is valid. For an AVL tree, it checks if all balance factors are within `[-1, 0, 1]`. For a Red-Black tree, it validates the black-heights and red-red rules. If a rule is violated, it outputs a raw "Symbolic Violation."

### Misconception Engine & Diagnosis Agent (`diagnosis_agent.py`, `misconception_engine.py`)
- **What it does:** Translates raw mathematical errors into human learning gaps.
- **How it works:** If a student performs a wrong operation, the Validation Agent yells "Balance Factor Error." The Diagnosis Agent takes this, looks at the tree state, and maps it to a psychological misconception. For example, it might diagnose that the student *"forgets to update heights after a Right-Right rotation"*. 

### Teaching Agent (`teaching_agent.py`)
- **What it does:** Acts as the direct Doubts Resolver.
- **How it works:** Uses Large Language Models (LLM) to generate conversational, pedagogical feedback. Instead of just giving a short error, the Teaching Agent looks at the Diagnosis Agent's output and gives a direct, simple explanation to help the student correct their own mistake.

### Concept Graph Agent (`concept_graph_agent.py`)
- **What it does:** The "Brain" of the tutoring system. It tracks exactly what the student knows.
- **How it works:** It maintains the Knowledge Graph (detailed below). It listens to the student's quiz results and updates their mastery scores, confidence metrics, and error rates over time.

### Quiz Agent (`quiz_agent.py`)
- **What it does:** The evaluator.
- **How it works:** It generates adaptive quizzes. If the Concept Graph Agent says the student is weak at "AVL Rotations," the Quiz Agent will pull or generate questions specifically targeting AVL Rotations to force the student to practice their weak spots.

---

## 3. Deep Dive: The Concept Knowledge Graph

The most powerful feature of the AI Tree Tutor is the **Concept Knowledge Graph**. This is not just a UI element; it is a mathematical model of the student's understanding.

### How the Graph is Structured
The graph is a **Directed Acyclic Graph (DAG)** of learning concepts defined in `misconception_engine.py`. Concepts are divided into four tiers:
1. **Prerequisites (Level 0):** Basic concepts like *BST Ordering*, *Recursion*, and *Pointer Manipulation*.
2. **Core Concepts (Level 1):** Foundational mechanics for specific trees, like *AVL Balance Factors* or *Red-Black Recolor Logic*.
3. **Operations (Level 2):** High-level algorithms like *AVL Insert* or *B-Tree Split*.
4. **Meta Concepts (Level 3):** Complex analysis like *Big-O Complexity* and *Tree Invariant Proofs*.

### Dependency & Prerequisite Logic
The edges in the graph represent dependencies. 
For example: `BST Search` → `AVL Insert`.
The system understands that a student **cannot** learn `AVL Insert` if they have a low mastery score in `BST Search`. If a student attempts a quiz on AVL Insert and fails, the system might look down the graph and realize the student actually forgot basic BST ordering.

### How Mastery is Updated
1. **Quizzes & Remediation Only:** The user's mastery of a concept is strictly updated when they answer a question in a **Quiz** or successfully complete a **Remediation Session**. (Note: Tree operations in the playground do not blindly update mastery, to prevent accidental clicks from skewing the student's true assessment).
2. **Success (Reward):** Answering a question correctly increases the node's mastery score by a small fraction.
3. **Mistake (Penalty & Propagation):** Answering incorrectly drops the score. **Crucially**, if a prerequisite concept's score drops, the penalty *propagates* upward. If your `BST Search` mastery drops to 0%, your `AVL Insert` mastery will also suffer a penalty because the foundation has cracked.

### Temporal Decay (The Forgetting Curve)
The Concept Graph implements an Ebbinghaus Forgetting Curve. If a student hasn't practiced "Red-Black Trees" in a long time, the Concept Graph Agent will slowly decay the mastery score for those nodes. This triggers the Quiz Agent to bring those topics back into the student's daily quizzes (Spaced Repetition).

---

## 4. The Remediation Loop
What happens when a student's mastery of a concept drops below 40%?
1. **Flagging:** The Concept Graph Agent flags the concept as a "Weakness."
2. **The Remediation Hub:** In the frontend UI, this concept appears in the Remediation Hub.
3. **Direct Chat:** The student clicks on it to start a targeted chat session. The Teaching Agent (LLM) takes over, aware of the student's exact misconception. 
4. **Resolution:** The LLM will quiz the student conversationally. Once the LLM is satisfied that the student understands the concept, it fires a `record_success` signal back to the Concept Graph, immediately bumping the mastery score back up and unlocking dependent concepts in the graph.

---

## 5. Frontend & Visualization
The frontend (React + Vite) uses **D3.js / React Flow** to render the Concept Knowledge Graph visually. 
- Nodes light up green when mastery is high.
- Nodes turn red or orange when mastery is low.
- Edges show the student exactly *why* they are struggling with advanced concepts by tracing the red lines back to fundamental prerequisite gaps.
