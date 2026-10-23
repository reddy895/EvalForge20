import { useState, useEffect } from 'react';
import { api } from '../services/api';

export interface OllamaState {
  reachable: boolean;
  version: string | null;
  installedModels: number;
  baseUrl: string;
  loading: boolean;
  error: string | null;
  suggestion: string | null;
  refresh: () => Promise<void>;
}

export function useOllamaStatus(): OllamaState {
  const [state, setState] = useState<OllamaState>({
    reachable: false,
    version: null,
    installedModels: 0,
    baseUrl: 'http://localhost:11434',
    loading: true,
    error: null,
    suggestion: null,
    refresh: async () => {},
  });

  const checkStatus = async () => {
    try {
      // First query dedicated Ollama health endpoint
      const ollamaHealth = await api.getOllamaHealth();
      let installedCount = 0;
      if (ollamaHealth.reachable) {
        try {
          const modelsRes = await api.getOllamaModels();
          installedCount = modelsRes.total || (modelsRes.models ? modelsRes.models.length : 0);
        } catch {
          installedCount = 0;
        }
      }

      setState((prev) => ({
        ...prev,
        reachable: ollamaHealth.reachable,
        version: ollamaHealth.version,
        installedModels: installedCount,
        baseUrl: ollamaHealth.base_url || 'http://localhost:11434',
        loading: false,
        error: ollamaHealth.reachable ? null : (ollamaHealth.suggestion || 'Ollama daemon is not reachable on localhost:11434'),
        suggestion: ollamaHealth.suggestion,
      }));
    } catch {
      // Fallback check on general health
      try {
        const genHealth = await api.getHealth();
        setState((prev) => ({
          ...prev,
          reachable: !!genHealth.ollama_reachable,
          version: genHealth.ollama_version || null,
          installedModels: genHealth.ollama_installed_models || 0,
          baseUrl: genHealth.ollama_base_url || 'http://localhost:11434',
          loading: false,
          error: genHealth.ollama_reachable ? null : 'Cannot connect to Ollama daemon. Start with `ollama serve`.',
          suggestion: 'Ensure Ollama is running at ' + (genHealth.ollama_base_url || 'http://localhost:11434'),
        }));
      } catch (err: any) {
        setState((prev) => ({
          ...prev,
          reachable: false,
          version: null,
          installedModels: 0,
          loading: false,
          error: err.message || 'EvalForge backend or Ollama unreachable',
          suggestion: 'Check backend status and run `ollama serve`',
        }));
      }
    }
  };

  useEffect(() => {
    checkStatus();
    setState((prev) => ({ ...prev, refresh: checkStatus }));
  }, []);

  return state;
}
