import { useState, useCallback } from 'react';
import { api } from '../api/client';
import type {
  CreateEvaluationPayload,
  RunSummary,
  RunDetailResponse,
  CaseResult,
} from '../api/types';

export interface UseEvaluationState {
  currentRun: RunDetailResponse | null;
  cases: CaseResult[];
  isRunning: boolean;
  error: string | null;
  startEvaluation: (payload: CreateEvaluationPayload) => Promise<RunSummary>;
  loadRun: (runId: string) => Promise<void>;
  reset: () => void;
}

export function useEvaluation(): UseEvaluationState {
  const [currentRun, setCurrentRun] = useState<RunDetailResponse | null>(null);
  const [cases, setCases] = useState<CaseResult[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const startEvaluation = useCallback(
    async (payload: CreateEvaluationPayload): Promise<RunSummary> => {
      setIsRunning(true);
      setError(null);
      try {
        const result = await api.createEvaluation(payload);
        return result;
      } catch (err: any) {
        const msg = err?.message || 'Failed to initiate evaluation run';
        setError(msg);
        throw err;
      } finally {
        setIsRunning(false);
      }
    },
    []
  );

  const loadRun = useCallback(async (runId: string) => {
    setIsRunning(true);
    setError(null);
    try {
      const [detailRes, casesRes] = await Promise.all([
        api.getEvaluation(runId),
        api.getCaseResults(runId, 200, 0),
      ]);
      setCurrentRun(detailRes);
      setCases(casesRes);
    } catch (err: any) {
      setError(err?.message || `Failed to load run ${runId}`);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const reset = useCallback(() => {
    setCurrentRun(null);
    setCases([]);
    setIsRunning(false);
    setError(null);
  }, []);

  return {
    currentRun,
    cases,
    isRunning,
    error,
    startEvaluation,
    loadRun,
    reset,
  };
}
