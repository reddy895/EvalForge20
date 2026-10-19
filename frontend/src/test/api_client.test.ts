import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '../services/api';

describe('Frontend API Client (services/api)', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('fetches health status correctly', async () => {
    const mockHealth = { status: 'healthy', app: 'EvalForge20', version: '2.0.0' };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    const result = await api.getHealth();
    expect(result).toEqual(mockHealth);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/health'),
      expect.any(Object)
    );
  });

  it('fetches model catalog with filter parameters', async () => {
    const mockModels = [
      {
        id: 'meta-llama/llama-3.1-8b-instruct',
        name: 'Llama 3.1 8B Instruct',
        provider: 'Meta',
        model_identifier: 'llama3.1:8b',
        family: 'Llama 3.1',
        context_window: 128000,
        is_local: true,
        is_installed: true,
        supports_tools: true,
        supports_structured_output: true,
        license: 'Llama 3.1 Community License',
        hardware_min_ram_gb: 16,
        recommended_tasks: ['coding', 'reasoning'],
        pricing_summary: 'Free Local Execution',
      },
    ];

    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockModels,
    } as Response);

    const result = await api.listModels({ provider: 'Meta', is_local: true });
    expect(result).toEqual(mockModels);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/models?provider=Meta&is_local=true'),
      expect.any(Object)
    );
  });

  it('fetches benchmark definitions', async () => {
    const mockBenchmarks = [
      {
        id: 'coding_basics',
        name: 'Python Function Implementations',
        task: 'coding',
        description: 'Tests Python functions',
        total_cases: 5,
      },
    ];

    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockBenchmarks,
    } as Response);

    const result = await api.listBenchmarks();
    expect(result).toEqual(mockBenchmarks);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/benchmarks'),
      expect.any(Object)
    );
  });

  it('handles Ollama daemon connection error safely without throwing', async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({ detail: 'Ollama daemon unreachable' }),
    } as Response);

    const status = await api.getOllamaStatus();
    expect(status.online).toBe(false);
    expect(status.models).toEqual([]);
  });

  it('throws descriptive error on failed API requests', async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ message: 'Model non-existent not found' }),
    } as Response);

    await expect(api.getModelProfile('non-existent')).rejects.toThrow('Model non-existent not found');
  });
});
