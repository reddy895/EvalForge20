import { useState, useCallback } from 'react';
import { api } from '../services/api';

export interface EvaluationRunnerState {
  running: boolean;
  progress: number;
  activeRunId: string | null;
  statusText: string | null;
  error: string | null;
  launchEvaluation: (payload: any) => Promise<any>;
}

export function useEvaluationRunner(): EvaluationRunnerState {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const launchEvaluation = useCallback(async (payload: any) => {
    setRunning(true);
    setProgress(5);
    setError(null);
    setStatusText('Dispatching evaluation run to backend...');

    try {
      // 1. Submit evaluation job to backend
      const initResp = await api.createEvaluation(payload);
      const runId = initResp.id;
      setActiveRunId(runId);
      setProgress(15);
      setStatusText('Running test cases on local Ollama...');

      // 2. Poll the run until completion with progressive status
      const completedRun = await api.pollEvaluation(runId, (pct) => {
        setProgress(pct);
        setStatusText(`Executing test cases (${pct}% complete)...`);
      });

      setProgress(100);
      setStatusText('Evaluation completed successfully.');
      return completedRun;
    } catch (err: any) {
      const msg = err.message || 'Evaluation run failed';
      setError(msg);
      setStatusText(`Error: ${msg}`);
      throw err;
    } finally {
      setRunning(false);
    }
  }, []);

  return { running, progress, activeRunId, statusText, error, launchEvaluation };
}
