import { useState, useEffect } from 'react';
import { api } from '../services/api';

export interface OllamaState {
  reachable: boolean;
  version: string | null;
  loading: boolean;
  error: string | null;
}

export function useOllamaStatus(): OllamaState {
  const [state, setState] = useState<OllamaState>({
    reachable: false,
    version: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    let mounted = true;
    api.getHealth()
      .then((data) => {
        if (mounted) {
          setState({
            reachable: data.status === 'healthy',
            version: data.version,
            loading: false,
            error: null,
          });
        }
      })
      .catch((err) => {
        if (mounted) {
          setState({
            reachable: false,
            version: null,
            loading: false,
            error: err.message || 'Ollama offline',
          });
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  return state;
}
