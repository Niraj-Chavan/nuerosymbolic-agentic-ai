# AI Tree Tutor — Architecture v2.0

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + D3)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Control   │ │Tree      │ │Explana-  │ │Animation│ │Quiz      │  │
│  │Panel     │ │Visualizer│ │tionPanel │ │Controller│ │Panel     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                        │  HTTP (REST) + SSE                         │
└────────────────────────┼────────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────────────┐
│              FastAPI (Uvicorn ASGI server)                          │
│  ┌─────────────────────┴──────────┐                                 │
│  │       API Router Layer         │                                 │
│  │  /api/tree/*  /api/quiz/*      │                                 │
│  │  /api/concepts/*  /api/ai/*    │                                 │
│  └─────────────────┬──────────────┘                                 │
│                    │                                                │
│  ┌─────────────────▼──────────────┐                                │
│  │   Operation Pipeline (Sync)    │  ◄── Fast path (<200ms)         │
│  │   TreeExec → Validation        │                                │
│  └─────────────────┬──────────────┘                                │
│                    │                                                │
│  ┌─────────────────▼──────────────┐                                │
│  │   AgentContext (Blackboard)    │  ◄── Shared state bus           │
│  └──┬──┬──┬──┬──┬──┬──┬──────────┘                                │
│     │  │  │  │  │  │  │                                            │
│  ┌──▼──▼──▼──▼──▼──▼──▼──┐  ┌──────────────────┐                  │
│  │   7 Agent Implement.   │  │  LLM Abstraction  │                  │
│  │   (BaseAgent protocol) │  │  Gemini/OpenAI/   │                  │
│  └────────┬───────────────┘  │  Claude adapter   │                  │
│           │                  └────────┬─────────┘                  │
│  ┌────────▼───────────────────────────▼─────────┐                  │
│  │           Background Workers (Celery/RQ)      │                  │
│  │   AI Teaching Generation │ Quiz Generation    │                  │
│  └──────────────────────────────────────────────┘                  │
│           │                                                        │
│  ┌────────▼────────────────────────────────────┐                   │
│  │         Data Layer                           │                   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │                   │
│  │  │PostgreSQL│ │  Redis   │ │  File Store   │ │                   │
│  │  │(persist) │ │ (cache)  │ │ (JSON data)   │ │                   │
│  │  └──────────┘ └──────────┘ └──────────────┘ │                   │
│  └─────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

## New Folder Structure

```
ai_tree_tutor/
├── ARCHITECTURE.md
├── backend/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # Entry point, lifespan, CORS
│   │   ├── config.py                  # Centralized config (env → settings)
│   │   ├── dependencies.py            # FastAPI Depends() wiring
│   │   │
│   │   ├── api/                       # Route layer (thin)
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # Aggregates all sub-routers
│   │   │   ├── tree_routes.py         # /api/tree/*
│   │   │   ├── concept_routes.py      # /api/concepts/*
│   │   │   ├── quiz_routes.py         # /api/quiz/*
│   │   │   └── analysis_routes.py     # /api/complexity, health
│   │   │
│   │   ├── core/                      # Core domain logic
│   │   │   ├── __init__.py
│   │   │   ├── operation_pipeline.py  # Pipeline orchestrator
│   │   │   └── tree_factory.py        # Tree registry/factory (decoupled)
│   │   │
│   │   ├── agents/                    # Agents — single interface
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Abstract BaseAgent
│   │   │   ├── tree_execution_agent.py
│   │   │   ├── validation_agent.py
│   │   │   ├── diagnosis_agent.py
│   │   │   ├── teaching_agent.py
│   │   │   ├── quiz_agent.py
│   │   │   ├── concept_graph_agent.py
│   │   │   ├── misconception_engine.py
│   │   │   └── step_recorder.py
│   │   │
│   │   ├── llm/                       # LLM abstraction layer
│   │   │   ├── __init__.py
│   │   │   ├── base_llm.py            # Abstract LLM interface
│   │   │   ├── gemini_engine.py       # Gemini implementation
│   │   │   └── prompt_templates.py    # All prompts externalized
│   │   │
│   │   ├── context/                   # Blackboard / context system
│   │   │   ├── __init__.py
│   │   │   └── agent_context.py       # AgentContext dataclass
│   │   │
│   │   ├── models/                    # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py             # API request/response models
│   │   │   ├── domain.py              # Domain entities
│   │   │   └── enums.py               # Enums (TreeType, Operation, etc.)
│   │   │
│   │   ├── database/                  # Persistence layer
│   │   │   ├── __init__.py
│   │   │   ├── connection.py          # DB connection mgmt
│   │   │   ├── repository.py          # Abstract Repository[T]
│   │   │   └── repositories/
│   │   │       ├── __init__.py
│   │   │       ├── tree_repository.py
│   │   │       ├── quiz_repository.py
│   │   │       └── concept_repository.py
│   │   │
│   │   ├── workers/                   # Background task processing
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── tasks.py               # AI generation tasks
│   │   │   └── quiz_tasks.py          # Quiz generation tasks
│   │   │
│   │   ├── trees/                     # Unchanged tree implementations
│   │   ├── validators/                # Unchanged validators
│   │   │
│   │   └── alembic/                   # Migrations
│   │
│   └── data/                          # Externalized static data
│       ├── fallback_explanations.json
│       ├── question_bank.json
│       └── violation_mappings.json
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── api.js                 # Axios client
│   │   ├── store/                     # Zustand state (NEW)
│   │   │   ├── useTreeStore.js
│   │   │   ├── useQuizStore.js
│   │   │   └── useConceptStore.js
│   │   ├── hooks/                     # Custom hooks (NEW)
│   │   │   ├── useOperation.js
│   │   │   ├── useAnimation.js
│   │   │   └── usePolling.js
│   │   ├── components/
│   │   │   ├── TreeVisualizer.jsx
│   │   │   ├── ControlPanel.jsx
│   │   │   ├── ExplanationPanel.jsx
│   │   │   ├── AnimationController.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── QuizPanel.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## Agent Communication Flow

```
                    AgentContext (Blackboard)
                    ┌────────────────────────────┐
                    │ session_id                  │
                    │ tree_type, operation, key   │
                    │ tree_instance, tree_export  │
                    │ operation_log               │
                    │ violations                  │
                    │ diagnoses                   │
                    │ teaching_materials          │
                    │ concept_updates             │
                    │ animation_steps             │
                    │ errors: List[str]           │
                    │ metadata: Dict              │
                    └────────────────────────────┘
                              ▲
                              │ read/write
                              │
┌─────────────┐  ┌───────────┴──────────┐  ┌─────────────┐
│   Router    │──▶  OperationPipeline    │──▶   Response   │
│   (API)     │   │                     │   │   Builder   │
└─────────────┘   └───┬───┬───┬───┬────┘   └─────────────┘
                      │   │   │   │
         ┌────────────┘   │   │   └────────────┐
         ▼                ▼   ▼                 ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │TreeExec  │   │Valid.    │   │Diagnosis │   │Teaching  │
   │Agent     │   │Agent     │   │Agent     │   │Agent     │
   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                      │
                                      │ (async)
                                      ▼
                                ┌──────────┐
                                │ Celery   │
                                │ Worker   │
                                └──────────┘
```

## Orchestration Design

```
Pipeline: Sequential with conditional branching + async offload

Synchronous chain (fast, <200ms):
  1. TreeExecutionAgent.process(ctx)    → populates tree, log
  2. ValidationAgent.process(ctx)       → populates violations
  3. Condition: violations exist?
     │  YES → continue to 4
     │  NO  → skip to 6
  4. DiagnosisAgent.process(ctx)        → populates diagnosis
     │  (enqueues async AI task for richer diagnosis)
  5. TeachingAgent.process(ctx)         → populates teaching
     │  (enqueues async AI task for deeper explanation)
  6. ConceptGraphAgent.process(ctx)     → updates mastery scores
  7. ResponseBuilder(ctx)               → builds API response
  8. Return immediate response + task IDs for async results

Async path (slow, >1s, via Celery):
  - diagnose_task(ctx_snapshot)         → Gemini AI diagnosis
  - teach_task(ctx_snapshot)            → Gemini AI explanation
  - quiz_task(ctx_snapshot)             → AI question generation
  → Results stored in Redis/cache
  → Frontend polls or receives via SSE
```

## Agent Base Interface

```python
class BaseAgent(ABC):
    """Every agent implements this single contract."""
    
    @abstractmethod
    async def process(self, ctx: AgentContext) -> AgentContext:
        """Process context, mutate it, return it."""
        ...
    
    @property
    def name(self) -> str:
        return self.__class__.__name__
```

## Pipeline Implementation

```python
class OperationPipeline:
    def __init__(self):
        self._handlers: list[tuple[BaseAgent, Callable[[AgentContext], bool]]] = []
    
    def add_handler(self, agent: BaseAgent, condition: Callable | None = None):
        self._handlers.append((agent, condition or (lambda ctx: True)))
    
    async def execute(self, ctx: AgentContext) -> AgentContext:
        for agent, condition in self._handlers:
            if condition(ctx):
                try:
                    ctx = await agent.process(ctx)
                except Exception as e:
                    ctx.errors.append(f"{agent.name}: {e}")
                    logger.exception(f"Pipeline error in {agent.name}")
                    break
        return ctx
```

## Key Improvements

### 1. Scalability
| Area | Before | After |
|------|--------|-------|
| State | In-memory dicts (lost on restart) | PostgreSQL + Redis (persistent) |
| LLM calls | Synchronous, blocks request | Async via Celery workers |
| API server | Single process | Multiple workers behind nginx |
| Session | Dict keyed by session_id | Proper DB-backed sessions |

### 2. Reduced Coupling
- **Before**: Agents imported directly in `main.py`, orchestration logic mixed with route handlers
- **After**: Agents implement `BaseAgent` protocol, communicate only through `AgentContext`, pipeline is configurable

### 3. Shared Context (Blackboard)
- Single `AgentContext` dataclass passed through pipeline
- Each agent reads what it needs, writes what it produces
- No direct agent-to-agent calls — all communication through context

### 4. Async Processing
- Fast path (tree ops, validation) stays synchronous
- Slow path (AI generation) offloaded to Celery workers
- Frontend polls for AI results or uses SSE

### 5. Maintainability
- Externalized data: `data/fallback_explanations.json`, `data/question_bank.json`
- Config management: `config.py` reads from env vars
- Prompt templates: `prompt_templates.py` centralizes all LLM prompts
- DB migrations: Alembic for schema versioning

### 6. Production Readiness
- Docker Compose with PostgreSQL, Redis, Celery, nginx
- Health checks, graceful shutdown, logging
- Rate limiting, request validation
- CORS configured per environment

## Database Schema (PostgreSQL)

```sql
-- Sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    tree_type TEXT NOT NULL,
    options JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tree State (snapshot per session)
CREATE TABLE tree_states (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    tree_type TEXT NOT NULL,
    tree_data JSONB NOT NULL,
    operation_log JSONB DEFAULT '[]',
    version INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Concept Mastery
CREATE TABLE concept_mastery (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    concept TEXT NOT NULL,
    mastery FLOAT DEFAULT 0.0,
    attempts INT DEFAULT 0,
    mistakes INT DEFAULT 0,
    UNIQUE(session_id, concept)
);

-- Quiz History
CREATE TABLE quiz_results (
    id SERIAL PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    quiz_data JSONB NOT NULL,
    score INT,
    total INT,
    answers JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Async Task Results
CREATE TABLE task_results (
    task_id TEXT PRIMARY KEY,
    session_id TEXT,
    task_type TEXT,
    result JSONB,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

## Frontend State Architecture (Zustand)

```javascript
// store/useTreeStore.js
const useTreeStore = create((set) => ({
  treeData: null,
  operationLog: [],
  validation: null,
  teaching: null,
  loading: false,
  performOperation: async (params) => {
    set({ loading: true });
    const res = await api.post('/api/tree/operate', params);
    set({ treeData: res.tree, validation: res.validation, ... });
    set({ loading: false });
  }
}));
```

## Environment Configuration

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_tree_tutor
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
GEMINI_API_KEY=...
LLM_PROVIDER=gemini        # gemini | openai | claude | mock
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

## Migration Path

1. **Phase 1** — Structural: Create new folder structure, implement `BaseAgent`, `AgentContext`, `OperationPipeline`. Keep old `main.py` working until new routes are tested.
2. **Phase 2** — Data: Add PostgreSQL + Alembic migrations. Migrate in-memory state to DB.
3. **Phase 3** — Async: Add Celery workers. Move AI generation to background tasks.
4. **Phase 4** — Frontend: Add Zustand stores. Extract API calls into hooks.
5. **Phase 5** — Production: Docker Compose, nginx, monitoring, CI/CD.
