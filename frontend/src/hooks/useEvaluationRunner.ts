import { useState, useCallback } from 'react';
import { api } from '../services/api';

export function useEvaluationRunner() {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const launchEvaluation = useCallback(async (payload: any) => {
    setRunning(true);
    setProgress(10);
    setError(null);
    try {
      const resp = await api.createEvaluation(payload);
      setProgress(100);
      return resp;
    } catch (err: any) {
      setError(err.message || 'Evaluation run failed');
      throw err;
    } finally {
      setRunning(false);
    }
  }, []);

  return { running, progress, error, launchEvaluation };
}
