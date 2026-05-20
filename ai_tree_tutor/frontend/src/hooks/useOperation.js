import { useCallback } from 'react';
import useTreeStore from '../store/useTreeStore';
import useConceptStore from '../store/useConceptStore';

export function useOperation() {
  const performOperation = useTreeStore((s) => s.performOperation);
  const fetchAnimationSteps = useTreeStore((s) => s.fetchAnimationSteps);
  const reset = useTreeStore((s) => s.reset);
  const loading = useTreeStore((s) => s.loading);
  const error = useTreeStore((s) => s.error);

  const fetchProgress = useConceptStore((s) => s.fetchProgress);

  const operate = useCallback(
    async (op) => {
      const res = await performOperation(op);
      if (res) {
        fetchProgress();
      }
      return res;
    },
    [performOperation, fetchProgress],
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
