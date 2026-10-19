import { useState, useCallback } from 'react';
import { api } from '../api/client';
import type { ComparisonResult } from '../api/types';

export interface UseComparisonState {
  comparison: ComparisonResult | null;
  isLoading: boolean;
  error: string | null;
  compareRuns: (
    baselineRunId: string,
    candidateRunId: string,
    allowDifferentDatasets?: boolean
  ) => Promise<ComparisonResult>;
  clear: () => void;
}

export function useComparison(): UseComparisonState {
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const compareRuns = useCallback(
    async (
      baselineRunId: string,
      candidateRunId: string,
      allowDifferentDatasets: boolean = false
    ): Promise<ComparisonResult> => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await api.compareRuns({
          baseline_run_id: baselineRunId,
          candidate_run_id: candidateRunId,
          allow_different_datasets: allowDifferentDatasets,
        });
        setComparison(result);
        return result;
      } catch (err: any) {
        const msg = err?.message || 'Failed to compare runs';
        setError(msg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const clear = useCallback(() => {
    setComparison(null);
    setError(null);
  }, []);

  return {
    comparison,
    isLoading,
    error,
    compareRuns,
    clear,
  };
}
