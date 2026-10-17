import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient } from '../api/client'

describe('apiClient', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    globalThis.fetch = vi.fn()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('fetches health status correctly', async () => {
    const mockHealth = { status: 'healthy', version: '0.1.0' }
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response)

    const result = await apiClient.getHealth()
    expect(result).toEqual(mockHealth)
    expect(globalThis.fetch).toHaveBeenCalledWith('/health', expect.any(Object))
  })

  it('fetches evaluations with query parameters', async () => {
    const mockRuns = [
      {
        id: 'eval_123',
        model_name: 'llama3:8b',
        dataset_name: 'trivia',
        status: 'COMPLETED',
        created_at: '2026-03-30T10:00:00Z',
      },
    ]
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockRuns,
    } as Response)

    const result = await apiClient.getEvaluations({ limit: 10, status: 'COMPLETED' })
    expect(result).toEqual(mockRuns)
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/v1/evaluations?limit=10&status=COMPLETED',
      expect.any(Object)
    )
  })

  it('handles Ollama daemon connection error safely', async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({ detail: 'Ollama daemon not reachable at http://localhost:11434' }),
    } as Response)

    const status = await apiClient.checkOllamaStatus()
    expect(status.connected).toBe(false)
    expect(status.models).toEqual([])
  })

  it('throws descriptive error on failed API requests', async () => {
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Run eval_unknown not found' }),
    } as Response)

    await expect(apiClient.getEvaluation('eval_unknown')).rejects.toThrow('Run eval_unknown not found')
  })

  it('fetches model catalog with provider query parameters', async () => {
    const mockCatalog = [
      {
        name: 'Qwen 2.5 3B',
        provider: 'ollama',
        model_identifier: 'qwen2.5:3b',
        is_local: true,
        modalities: ['text'],
        supports_tools: true,
        supports_structured_output: true,
        connection_status: 'online',
      },
    ]
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockCatalog,
    } as Response)

    const result = await apiClient.listCatalogModels({ provider: 'ollama', is_local: true })
    expect(result).toEqual(mockCatalog)
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/v1/catalog/models?provider=ollama&is_local=true',
      expect.any(Object)
    )
  })

  it('fetches task and complexity analysis for an evaluation run', async () => {
    const mockAnalysis = {
      run_id: 'run-101',
      model_identifier: 'qwen2.5:3b',
      categories: [
        { category: 'Reasoning', total_cases: 10, pass_rate: 0.9, mean_latency_ms: 120, failure_rate: 0.1, estimated_cost_per_task: 0, representative_failures: [] }
      ],
      complexity_bands: [
        { band: 'low', case_count: 5, pass_rate: 1.0, mean_latency_ms: 80, has_sufficient_data: true }
      ]
    }
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalysis,
    } as Response)

    const result = await apiClient.getTaskAnalysis('run-101')
    expect(result).toEqual(mockAnalysis)
    expect(globalThis.fetch).toHaveBeenCalledWith('/v1/task-analysis/run-101', expect.any(Object))
  })
})
