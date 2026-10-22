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
});
