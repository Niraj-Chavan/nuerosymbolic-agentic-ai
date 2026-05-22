import { useCallback } from 'react';
import useTreeStore from '../store/useTreeStore';
import useConceptStore from '../store/useConceptStore';
import useTutorStore from '../store/useTutorStore';

export function useOperation() {
  const performOperation = useTreeStore((s) => s.performOperation);
  const fetchAnimationSteps = useTreeStore((s) => s.fetchAnimationSteps);
  const reset = useTreeStore((s) => s.reset);
  const loading = useTreeStore((s) => s.loading);
  const error = useTreeStore((s) => s.error);

  const fetchProgress = useConceptStore((s) => s.fetchProgress);
  const fetchGraph = useConceptStore((s) => s.fetchGraph);
  const fetchWeakConceptsConcept = useConceptStore((s) => s.fetchWeakConcepts);
  const fetchWeakConceptsTutor = useTutorStore((s) => s.fetchWeakConcepts);

  const operate = useCallback(
    async (op) => {
      const res = await performOperation(op);
      if (res) {
        fetchProgress();
        fetchGraph();
        fetchWeakConceptsConcept();
        fetchWeakConceptsTutor();
      }
      return res;
    },
    [performOperation, fetchProgress, fetchGraph, fetchWeakConceptsConcept, fetchWeakConceptsTutor],
  );

  const operateWithSteps = useCallback(
    async (op) => {
      const res = await fetchAnimationSteps(op);
      return res;
    },
    [fetchAnimationSteps],
  );

  return { operate, operateWithSteps, reset, loading, error };
}
