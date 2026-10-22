import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { ModelProfile } from '../types';

export function useModelDiscovery() {
  const [models, setModels] = useState<ModelProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getModels();
      setModels(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load models');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const refresh = useCallback(async () => {
    try {
      await api.refreshModels();
      await fetchModels();
    } catch (err: any) {
      setError(err.message || 'Failed to refresh models');
    }
  }, [fetchModels]);

  return { models, loading, error, refresh };
}
