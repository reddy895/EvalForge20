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
  connectivityState: string;
  installedLocally: boolean;
  availableModels: string[];
  modelReady: boolean | null;
  lastChecked: string | null;
  refresh: () => Promise<void>;
  checkModelReadiness: (modelId: string) => Promise<{ ready: boolean; hint?: string }>;
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
    connectivityState: 'connecting',
    installedLocally: false,
    availableModels: [],
    modelReady: null,
    lastChecked: null,
    refresh: async () => {},
    checkModelReadiness: async () => ({ ready: false }),
  });

  const checkModelReadiness = async (modelId: string) => {
    try {
      const res = await api.getOllamaHealth(modelId);
      return {
        ready: !!res.model_ready,
        hint: res.suggestion || undefined,
      };
    } catch {
      return { ready: false, hint: 'Failed to verify model readiness' };
    }
  };

  const checkStatus = async () => {
    try {
      // First query dedicated Ollama health endpoint
      const ollamaHealth = await api.getOllamaHealth();
      let installedCount = ollamaHealth.installed_models_count || 0;
      let availModels = ollamaHealth.available_models || [];

      if (ollamaHealth.reachable && installedCount === 0) {
        try {
          const modelsRes = await api.getOllamaModels();
          installedCount = modelsRes.total || (modelsRes.models ? modelsRes.models.length : 0);
          availModels = modelsRes.models ? modelsRes.models.map((m: any) => m.id || m.name) : availModels;
        } catch {
          // Keep count
        }
      }

      const connState = ollamaHealth.connectivity_state || (
        ollamaHealth.reachable
          ? (installedCount > 0 ? 'ready' : 'reachable_no_models')
          : (ollamaHealth.installed_locally ? 'installed_not_running' : 'connection_refused')
      );

      setState((prev) => ({
        ...prev,
        reachable: ollamaHealth.reachable,
        version: ollamaHealth.version,
        installedModels: installedCount,
        availableModels: availModels,
        connectivityState: connState,
        installedLocally: !!ollamaHealth.installed_locally,
        modelReady: ollamaHealth.model_ready ?? null,
        baseUrl: ollamaHealth.base_url || 'http://localhost:11434',
        loading: false,
        lastChecked: ollamaHealth.last_checked_at || new Date().toLocaleTimeString(),
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
          connectivityState: genHealth.ollama_reachable ? 'ready' : 'connection_refused',
          lastChecked: new Date().toLocaleTimeString(),
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
          connectivityState: 'connection_refused',
          lastChecked: new Date().toLocaleTimeString(),
          error: err.message || 'EvalForge backend or Ollama unreachable',
          suggestion: 'Check backend status and run `ollama serve`',
        }));
      }
    }
  };

  useEffect(() => {
    checkStatus();
    setState((prev) => ({ ...prev, refresh: checkStatus, checkModelReadiness }));
  }, []);

  return state;
}
