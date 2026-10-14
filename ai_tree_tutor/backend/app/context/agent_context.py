from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineEvent:
    type: str
    agent: str
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class AgentContext:
    # --- Request fields ---
    session_id: str = "default"
    tree_type: str = ""
    operation: str = ""
    key: Optional[int] = None
    options: Dict[str, Any] = field(default_factory=dict)

    # --- Pipeline stage outputs ---
    tree_instance: Optional[Any] = None
    tree_export: Optional[Any] = None
    operation_log: List[Dict[str, Any]] = field(default_factory=list)

    found: Optional[bool] = None

    search_path: List[Dict[str, Any]] = field(default_factory=list)

    violations: List[Dict[str, Any]] = field(default_factory=list)
    validation_valid: bool = True
    affected_nodes: List[int] = field(default_factory=list)

    diagnoses: List[Dict[str, Any]] = field(default_factory=list)
    teaching_materials: List[Dict[str, Any]] = field(default_factory=list)
    complexity: Optional[Dict[str, Any]] = None

    concept_updates: List[Dict[str, Any]] = field(default_factory=list)

    animation_steps: List[Dict[str, Any]] = field(default_factory=list)

    # --- Async task tracking ---
    async_task_ids: Dict[str, str] = field(default_factory=dict)

    # --- Error handling ---
    errors: List[str] = field(default_factory=list)

    # --- Metadata ---
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ==================================================================
    # Shared memory & session persistence (new)
    # ==================================================================

    shared_memory: Dict[str, Any] = field(default_factory=dict)

    session_state: Dict[str, Any] = field(default_factory=dict)

    event_log: List[PipelineEvent] = field(default_factory=list)

    pipeline_start_time: float = 0.0

    # ==================================================================
    # Properties
    # ==================================================================

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def event_count(self) -> int:
        return len(self.event_log)

    @property
    def pipeline_duration_ms(self) -> float:
        if self.pipeline_start_time == 0:
            return 0.0
        return (time.time() - self.pipeline_start_time) * 1000

    # ==================================================================
    # Event recording
    # ==================================================================

    def record_event(
        self,
        event_type: str,
        agent: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
    ) -> None:
        self.event_log.append(PipelineEvent(
            type=event_type,
            agent=agent,
            timestamp=time.time(),
            data=data or {},
            duration_ms=duration_ms,
        ))

    # ==================================================================
    # Shared memory operations
    # ==================================================================

    def store(self, key: str, value: Any) -> None:
        self.shared_memory[key] = value

    def retrieve(self, key: str, default: Any = None) -> Any:
        return self.shared_memory.get(key, default)

    def store_session(self, key: str, value: Any) -> None:
        self.session_state[key] = value

    def retrieve_session(self, key: str, default: Any = None) -> Any:
        return self.session_state.get(key, default)

    # ==================================================================
    # Serialization
    # ==================================================================

    def snapshot(self) -> dict:
        return {
            "session_id": self.session_id,
            "tree_type": self.tree_type,
            "operation": self.operation,
            "key": self.key,
            "options": self.options,
            "violations": self.violations,
            "diagnoses": self.diagnoses,
            "teaching_materials": self.teaching_materials,
            "concept_updates": self.concept_updates,
            "errors": self.errors,
            "metadata": self.metadata,
            "shared_memory_keys": list(self.shared_memory.keys()),
            "session_state_keys": list(self.session_state.keys()),
            "event_count": self.event_count,
        }

    def merge_snapshot(self, data: dict) -> None:
        if "violations" in data:
            self.violations = data["violations"]
        if "diagnoses" in data:
            self.diagnoses = data["diagnoses"]
        if "metadata" in data:
            self.metadata.update(data["metadata"])
        if "shared_memory_keys" in data:
            pass
