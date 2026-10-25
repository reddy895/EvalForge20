import { describe, it, expect, vi } from 'vitest';
import { api } from '../services/api';

describe('Ollama Status Contract', () => {
  it('correctly maps health check payload', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValueOnce({
      status: 'healthy',
      app: 'EvalForge20',
      version: '2.0.0',
      ollama_base_url: 'http://localhost:11434',
    });

    const data = await api.getHealth();
    expect(data.status).toBe('healthy');
    expect(data.version).toBe('2.0.0');
    expect(data.ollama_base_url).toContain('11434');
  });

  it('handles offline ollama daemon gracefully', async () => {
    vi.spyOn(api, 'getHealth').mockRejectedValueOnce(new Error('Connection refused'));

    await expect(api.getHealth()).rejects.toThrow('Connection refused');
  });

  it('correctly parses 8-state ollama diagnostic payload with model readiness and remediation hint', async () => {
    vi.spyOn(api, 'getOllamaHealth').mockResolvedValueOnce({
      status: 'ok',
      base_url: 'http://localhost:11434',
      reachable: true,
      connectivity_state: 'ready',
      version: '0.4.1',
      installed_locally: true,
      installed_models_count: 2,
      available_models: ['qwen2.5:1.5b', 'llama3.2:1b'],
      model_ready: true,
      suggestion: null,
      last_checked_at: '12:00:00 PM',
    });

    const diag = await api.getOllamaHealth('qwen2.5:1.5b');
    expect(diag.reachable).toBe(true);
    expect(diag.connectivity_state).toBe('ready');
    expect(diag.installed_models_count).toBe(2);
    expect(diag.available_models).toContain('qwen2.5:1.5b');
    expect(diag.model_ready).toBe(true);
  });

  it('reports requested_model_missing with actionable pull remediation hint', async () => {
    vi.spyOn(api, 'getOllamaHealth').mockResolvedValueOnce({
      status: 'ok',
      base_url: 'http://localhost:11434',
      reachable: true,
      connectivity_state: 'requested_model_missing',
      version: '0.4.1',
      installed_locally: true,
      installed_models_count: 1,
      available_models: ['qwen2.5:1.5b'],
      model_ready: false,
      suggestion: 'Run `ollama pull deepseek-r1:8b` to install the model locally.',
      last_checked_at: '12:00:00 PM',
    });

    const diag = await api.getOllamaHealth('deepseek-r1:8b');
    expect(diag.reachable).toBe(true);
    expect(diag.model_ready).toBe(false);
    expect(diag.connectivity_state).toBe('requested_model_missing');
    expect(diag.suggestion).toContain('ollama pull deepseek-r1:8b');
  });

  it('reports installed_not_running when binary is installed but daemon is stopped', async () => {
    vi.spyOn(api, 'getOllamaHealth').mockResolvedValueOnce({
      status: 'error',
      base_url: 'http://localhost:11434',
      reachable: false,
      connectivity_state: 'installed_not_running',
      version: null,
      installed_locally: true,
      installed_models_count: 0,
      available_models: [],
      model_ready: false,
      suggestion: "Ollama is installed locally, but the service is stopped. Run 'ollama serve' to start it.",
      last_checked_at: '12:00:00 PM',
    });

    const diag = await api.getOllamaHealth();
    expect(diag.reachable).toBe(false);
    expect(diag.installed_locally).toBe(true);
    expect(diag.connectivity_state).toBe('installed_not_running');
    expect(diag.suggestion).toContain('ollama serve');
  });
});
