# AI Tree Tutor

**Neuro-Symbolic Agentic AI System for Learning Advanced Tree Data Structures**

> Concept-level misconception detection and adaptive teaching powered by Google Gemini + symbolic validation.

---

## 🏗️ Architecture

```
User → Frontend (React + D3.js)
         ↓ API
      FastAPI Backend
         ↓
  Agentic Pipeline:
    1. Tree Execution Agent     → performs insert/delete/search
    2. Symbolic Validation Agent → checks tree invariants (rules)
    3. Misconception Diagnosis   → neural (Gemini) + symbolic
    4. Teaching Agent            → generates explanations
    5. Concept Graph Agent       → tracks mastery & progress
```

## 🌳 Supported Trees

| Tree | Operations | Validation |
|------|-----------|-----------|
| AVL Tree | insert, delete, search | Balance factor, BST ordering, height |
| Red-Black Tree | insert, delete, search | Root color, red-red, black height |
| Binary Heap | insert, delete, search | Heap property (min/max) |
| Segment Tree | insert, delete, search, range query | Range sum consistency |
| B-Tree | insert, delete, search | Order, child count, leaf depth |
| B+ Tree | insert, delete, search | Order, leaf linkage, child count |

## 🚀 Quick Start

### Backend

```bash
cd ai_tree_tutor/backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # Add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd ai_tree_tutor/frontend
npm install
npm run dev                    # http://localhost:3000
```

## 🔑 Environment

Create `backend/.env`:

```
GEMINI_API_KEY=your_key_here
```

> The system works without an API key (uses rule-based fallbacks).

## 📂 Project Structure

```
ai_tree_tutor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + all routes
│   │   ├── ai/
│   │   │   └── gemini_engine.py  # Gemini API integration
│   │   ├── agents/
│   │   │   ├── tree_execution_agent.py
│   │   │   ├── validation_agent.py
│   │   │   ├── diagnosis_agent.py
│   │   │   ├── teaching_agent.py
│   │   │   └── concept_graph_agent.py
│   │   ├── trees/
│   │   │   ├── avl.py
│   │   │   ├── red_black.py
│   │   │   ├── heap.py
│   │   │   ├── segment_tree.py
│   │   │   ├── btree.py
│   │   │   └── bplus_tree.py
│   │   ├── validators/
│   │   │   ├── avl_validator.py
│   │   │   ├── rb_validator.py
│   │   │   └── btree_validator.py
│   │   ├── concept_graph/
│   │   │   └── graph_manager.py
│   │   └── database/
│   │       └── models.py        # Pydantic schemas
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── index.css
    │   ├── api/api.js
    │   └── components/
    │       ├── TreeVisualizer.jsx
    │       ├── ControlPanel.jsx
    │       ├── ExplanationPanel.jsx
    │       └── Dashboard.jsx
    └── package.json
```

## 🔌 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/trees` | List supported trees & operations |
| POST | `/api/tree/operate` | Execute operation (full pipeline) |
| POST | `/api/tree/reset` | Reset a tree |
| GET | `/api/tree/export/{type}` | Export current tree state |
| GET | `/api/concepts` | Full concept knowledge graph |
| GET | `/api/concepts/progress` | Learning progress summary |
| GET | `/api/concepts/weak` | Weak concept areas |
| GET | `/api/complexity/{tree}/{op}` | Complexity analysis |
