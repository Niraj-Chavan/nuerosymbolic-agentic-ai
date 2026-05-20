import { useEffect, useRef, useCallback } from 'react';
import { getTaskResult } from '../api/api';

export function usePolling(taskId, interval = 2000, onResult, onError) {
  const savedCallback = useRef(onResult);

  useEffect(() => {
    savedCallback.current = onResult;
  }, [onResult]);

  const poll = useCallback(async () => {
    if (!taskId) return;
    try {
      const res = await getTaskResult(taskId);
      if (res.status === 'completed' && savedCallback.current) {
        savedCallback.current(res);
      } else if (res.status === 'failed' && onError) {
        onError(res.error);
      }
    } catch (err) {
      if (onError) onError(err.message);
    }
  }, [taskId, onError]);

  useEffect(() => {
    if (!taskId) return;
    const id = setInterval(poll, interval);
    return () => clearInterval(id);
  }, [taskId, interval, poll]);
}
