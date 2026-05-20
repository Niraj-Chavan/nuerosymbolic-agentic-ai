# AI Tree Tutor — Complete Project Overview

This document provides a comprehensive, high-level overview of the entire AI Tree Tutor project. It explains the purpose and functionality of every major component, how the trees are structured, how the intelligent agents work together, and how the frontend and backend communicate.

---

## 1. High-Level Architecture
The AI Tree Tutor is a full-stack educational application designed to teach complex data structures (like AVL trees, B-trees, Red-Black trees etc.) using a "Neuro-Symbolic Agentic" approach. 

- **Backend (Python / FastAPI):** Handles the mathematical exactness of the data structures (Symbolic AI) combined with the reasoning and explanatory power of Large Language Models (Neural/Generative AI).
- **Frontend (React / Vite):** Provides an interactive, animated visual interface where users can play with data structures, read AI explanations, and take quizzes.

### The Agentic Pipeline 
Whenever a user performs an operation (e.g., "Insert 50 into AVL Tree"), the backend runs a specific pipeline:
1. **Execution:** The tree logic runs the operation.
2. **Validation:** Invariants (rules of the tree) are checked.
3. **Diagnosis:** If the student makes a mistake (or if we are just explaining the process), an AI agent diagnoses what happened based on the rules.
4. **Teaching:** Another AI agent generates a human-readable, educational explanation.
5. **Concept Graph Update:** The system records what the student understands or struggles with to adapt future interactions.

---

## 2. Backend Components (`backend/app/`)

### 2.1 Trees (`backend/app/trees/`)
This module contains the pure algorithmic implementations of various complex data structures. They handle the underlying data manipulation without worrying about the AI or UI.
- **AVL Tree (`avl.py`):** A self-balancing binary search tree. Operations like insert/delete automatically trigger left/right rotations to maintain a strict balance factor.
- **Red-Black Tree (`red_black.py`):** A self-balancing BST using color properties (red/black) to ensure the tree remains approximately balanced, guaranteeing O(log n) operations.
- **B-Tree & B+ Tree (`btree.py`, `bplus_tree.py`):** Multi-way search trees optimized for systems that read/write large blocks of data. Nodes can have multiple children and keys.
- **Heap (`heap.py`):** A specialized tree-based structure serving as a priority queue (min-heap or max-heap).
- **Segment Tree (`segment_tree.py`):** Used for efficiently answering range queries (e.g., sum or minimum of an array segment) and updating elements.

### 2.2 Validators (`backend/app/validators/`)
Validators are "rule checkers." After an operation in the trees, validators ensure the mathematical properties of the tree still hold.
- **AVL Validator:** Checks if the balance factor of every node is between -1 and 1, and that BST ordering is correct.
- **Red-Black Validator:** Checks root color, red node children colors, and black-depth paths.
- **B-Tree Validator:** Checks maximum/minimum keys per node and ensures all leaf nodes are at the same depth.

### 2.3 Intelligent Agents (`backend/app/agents/`)
The agents are the "brains" of the tutoring system. They bridge the gap between hardcoded data structures and the student.
- **Tree Execution Agent (`tree_execution_agent.py`):** The manager that receives a command from the UI and executes it on the correct tree instance.
- **Validation Agent (`validation_agent.py`):** Triggers the tree validators to find structural violations or errors in the current tree state.
- **Diagnosis Agent (`diagnosis_agent.py`):** Takes any violations calculated by the Validation Agent and uses an LLM (Gemini) to determine *why* a conceptual error occurred (e.g., "The student forgot to do a right rotation").
- **Teaching Agent (`teaching_agent.py`):** Takes the output of the Diagnosis Agent and uses the LLM to generate a pedagogical, encouraging explanation to teach the student how to fix the error.
- **Quiz Agent (`quiz_agent.py`):** Generates adaptive quizzes. It looks at the student's weaknesses and asks tailored questions to test their knowledge.
- **Concept Graph Agent (`concept_graph_agent.py`):** Maintains a knowledge graph. It connects concepts (e.g., "BST Insertion" -> "AVL Rotations") and tracks the student's mastery level for each node.
- **Step Recorder (`step_recorder.py`):** Instead of just showing the final tree, this records intermediate snapshots during an insertion/deletion so the frontend can animate the process step-by-step.

### 2.4 Concept Graph (`backend/app/concept_graph/`)
- **Graph Manager (`graph_manager.py`):** Interacts with the Concept Graph Agent to update the student's mastery tracker after every operation or quiz answer.

### 2.5 AI Engine (`backend/app/ai/gemini_engine.py`)
- Acts as the interface to the Google Gemini Large Language Model. It structures prompts safely and parses the AI's complex JSON responses for the agents to use.

### 2.6 Main Entry Point (`backend/app/main.py`)
- The FastAPI application routing layer. It defines endpoints like `/api/tree/operate` (to do tree math and get AI feedback), `/api/quiz/generate` (to get a quiz), and handles all HTTP requests from the frontend.

---

## 3. Frontend Components (`frontend/src/`)

The frontend is a React application styled primarily with TailwindCSS (or standard CSS), utilizing modular components to build the UI.

### 3.1 Components (`frontend/src/components/`)
- **ControlPanel.jsx:** Contains inputs and buttons where the user types numbers to insert, delete, or search in the tree. It sends the requests to the backend.
- **TreeVisualizer.jsx:** Using dynamic SVG or Canvas drawing, this component reads the JSON representation of the tree from the backend and plots the nodes and connecting edges visually on the screen.
- **AnimationController.jsx:** Given the step-by-step data from the `step_recorder`, this provides a timeline (Play, Pause, Next Step, Prev Step) so the user can watch the tree undergo internal changes like rebalancing.
- **ExplanationPanel.jsx:** A textual sidebar or overlay where the Diagnosis and Teaching Agent's output is displayed to the user. This is where the "Tutor" talks to the student.
- **QuizPanel.jsx:** The interface for the student to take generated quizzes, submit answers, and see immediate AI-driven feedback.
- **Dashboard.jsx:** Shows the student's overall learning progress, often pulling data from the Concept Graph to show areas of strength and weakness.

### 3.2 Services (`frontend/src/api/api.js`)
- Contains the Axios or Fetch wrappers that communicate with the FastAPI backend. It abstracts endpoints like `operateTree(type, operation, key)` into simple async Javascript functions.

---

## Summary of the Flow
1. **Student action:** The student clicks "Insert 15" on the frontend `ControlPanel.jsx`.
2. **API Call:** The frontend calls the backend `/api/tree/operate-steps` (or standard operate).
3. **Execution & Recording:** The `TreeExecutionAgent` calls the underlying Python `avl.py` code. The `step_recorder` logs every sub-action (like rotations).
4. **Validation:** The `ValidationAgent` ensures the tree is mathematically sound.
5. **AI Analysis:** The `DiagnosisAgent` and `TeachingAgent` formulate an explanation of what just happened.
6. **Concept Update:** The `GraphManager` boosts the student's mastery score for "Insertion".
7. **Response & Animation:** The backend packages the tree visual data, the AI explanations, and the animation steps, sending it back to the frontend.
8. **Visual Render:** `TreeVisualizer.jsx` updates the nodes, while `AnimationController.jsx` plays the steps, and `ExplanationPanel.jsx` shows the text.
