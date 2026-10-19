import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type { DetailedModel, OllamaDiagnosticReport } from '../api/types';

export interface UseModelsState {
  models: DetailedModel[];
  ollamaStatus: OllamaDiagnosticReport | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useModels(): UseModelsState {
  const [models, setModels] = useState<DetailedModel[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaDiagnosticReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [modelsRes, statusRes] = await Promise.all([
        api.listModels().catch(() => []),
        api.getOllamaStatus().catch(() => null),
      ]);
      setModels(modelsRes);
      setOllamaStatus(statusRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch models');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return {
    models,
    ollamaStatus,
    isLoading,
    error,
    refresh: fetchModels,
  };
}
