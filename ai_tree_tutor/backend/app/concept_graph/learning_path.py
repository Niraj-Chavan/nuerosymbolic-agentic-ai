from __future__ import annotations
from typing import Any, Dict, List, Optional
import networkx as nx
from app.agents.concept_graph_agent import ConceptGraphAgent

class LearningPathGenerator:
    """
    Generates personalized, optimized learning sequences using the ConceptGraph.
    Uses topological sorting, mastery filters, difficulty balancing, and strategic assessments.
    """
    def __init__(self, concept_agent: ConceptGraphAgent):
        self.concept_agent = concept_agent

    def generate_path(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Generate a personalized study roadmap for a student.
        - Identifies weak concepts (mastery < 0.8)
        - Performs topological sort on prerequisites
        - Computes difficulty curves, time estimates, and checkpoint intervals
        """
        graph = self.concept_agent.graph
        mastery_data = {}
        
        # Pull latest mastery from the concept agent
        for node in graph.nodes:
            mastery_data[node] = self.concept_agent.get_mastery(node)

        # We want to identify target nodes that are weak (mastery < 0.8)
        # and trace their dependencies
        weak_nodes = [node for node, m in mastery_data.items() if m < 0.8]
        
        # If no weak nodes, we can suggest advanced concepts or just include all of them
        if not weak_nodes:
            weak_nodes = list(graph.nodes)

        # Build a subgraph of weak nodes and all their ancestors (prerequisites)
        nodes_to_include = set()
        for node in weak_nodes:
            visited = set()
            def collect(n):
                if n in visited:
                    return
                visited.add(n)
                # Successors are the prerequisites of n
                for prereq in graph.successors(n):
                    collect(prereq)
            collect(node)
            nodes_to_include.update(visited)

        # Create a dependency subgraph with reversed edges (so prereq -> dependent)
        dependency_subgraph = nx.DiGraph()
        for node in nodes_to_include:
            dependency_subgraph.add_node(node)
            for prereq in graph.successors(node):
                if prereq in nodes_to_include:
                    # Edge direction: prereq -> node
                    dependency_subgraph.add_edge(prereq, node)

        # Run topological sort to get correct sequence order
        try:
            sequence = list(nx.topological_sort(dependency_subgraph))
        except nx.NetworkXUnfeasible:
            # Cycle detected (fallback to node list)
            sequence = list(nodes_to_include)

        # Build the final path
        path = []
        estimated_time = 0.0
        difficulty_curve = []
        
        for concept_id in sequence:
            concept_data = self.concept_agent.get_concept_data(concept_id)
            if not concept_data:
                continue
                
            m = concept_data["mastery"]
            difficulty = concept_data["difficulty"]
            is_hub = concept_data["is_hub"]
            
            # Status: mastered (if >=0.8), review (if 0.5 <= m < 0.8), or learn (if <0.5)
            if m >= 0.8:
                status = "mastered"
                time_est = 2.0  # minutes for quick review check
            elif m >= 0.5:
                status = "review"
                time_est = round(10.0 * difficulty + (5.0 if is_hub else 0.0), 1)
            else:
                status = "learn"
                time_est = round(20.0 * difficulty + (10.0 if is_hub else 0.0), 1)

            estimated_time += time_est
            difficulty_curve.append({
                "concept_id": concept_id,
                "difficulty": difficulty
            })
            
            # Suggest teaching modality
            if status == "learn":
                modality = "visual_text"
            elif status == "review":
                modality = "socratic_practice"
            else:
                modality = "quiz"

            path.append({
                "concept_id": concept_id,
                "name": concept_data["name"],
                "status": status,
                "mastery": m,
                "difficulty": difficulty,
                "is_hub": is_hub,
                "estimated_time_mins": time_est,
                "suggested_modality": modality,
                "reason": f"Prerequisite gap or weak mastery ({m:.0%})" if status != "mastered" else "Mastered prerequisite"
            })

        # Insert checkpoints (strategic review points) every 3 items
        checkpoints = []
        for i in range(len(path)):
            if (i + 1) % 3 == 0 or i == len(path) - 1:
                checkpoints.append({
                    "after_index": i,
                    "concept_id": path[i]["concept_id"],
                    "assessment_type": "checkpoint_quiz",
                    "description": f"Checkpoint assessment covering {', '.join([p['name'] for p in path[max(0, i-2):i+1]])}"
                })

        return {
            "sequence": path,
            "estimated_time_mins": round(estimated_time, 1),
            "difficulty_curve": difficulty_curve,
            "checkpoints": checkpoints
        }
