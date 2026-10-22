/**
 * EvalForge20 — Typed API Service Client
 * Connects frontend UI to FastAPI backend with graceful fallback.
 */

import {
  ModelProfile,
  ProviderDetail,
  AnalyticsOverview,
  CommitAnalytics,
  EvaluationRun,
  DatasetItem,
} from '../types';
import { SAMPLE_MODELS } from '../data/models';

const API_BASE = '/api';

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    };

    try {
      const resp = await fetch(url, { ...options, headers });
      if (!resp.ok) {
        let errorMsg = resp.statusText ? `HTTP ${resp.status}: ${resp.statusText}` : `HTTP ${resp.status}`;
        try {
          const errData = await resp.json();
          if (errData?.error?.message) {
            errorMsg = errData.error.message;
          } else if (errData?.detail) {
            errorMsg = errData.detail;
          }
        } catch {
          // Keep default message
        }
        throw new Error(errorMsg);
      }
      return await resp.json();
    } catch (err: any) {
      console.warn(`[API] Call to ${url} failed:`, err?.message || err);
      throw err;
    }
  }

  // Health
  async getHealth(): Promise<{ status: string; app: string; version: string; ollama_base_url: string }> {
    return this.request('/health');
  }

  // Providers
  async getProviders(): Promise<ProviderDetail[]> {
    try {
      const data = await this.request<{ total: number; providers: ProviderDetail[] }>('/providers/details');
      return data.providers;
    } catch {
      // Fallback status
      return [
        {
          name: 'ollama',
          display_name: 'Ollama (Local)',
          provider_type: 'local',
          implementation_status: 'implemented_and_tested',
          healthy: false,
          is_configured: true,
          default: true,
          setup_instructions: 'Start Ollama daemon via "ollama serve".',
          supported_models_count: 5,
        },
        {
          name: 'mock',
          display_name: 'Deterministic Mock',
          provider_type: 'local',
          implementation_status: 'implemented_and_tested',
          healthy: true,
          is_configured: true,
          default: false,
          setup_instructions: 'Built-in offline testing provider.',
          supported_models_count: 3,
        },
      ];
    }
  }

  // Models
  async getModels(params?: {
    query?: string;
    provider?: string;
    task?: string;
    is_local?: boolean;
    is_installed?: boolean;
    supports_tools?: boolean;
    supports_structured_output?: boolean;
    sort_by?: string;
    offset?: number;
    limit?: number;
  }): Promise<{ models: ModelProfile[]; total: number }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.query) queryParams.set('query', params.query);
      if (params?.provider && params.provider !== 'all') queryParams.set('provider', params.provider);
      if (params?.task && params.task !== 'all') queryParams.set('task', params.task);
      if (params?.is_local !== undefined) queryParams.set('is_local', String(params.is_local));
      if (params?.is_installed !== undefined) queryParams.set('is_installed', String(params.is_installed));
      if (params?.supports_tools !== undefined) queryParams.set('supports_tools', String(params.supports_tools));
      if (params?.supports_structured_output !== undefined) queryParams.set('supports_structured_output', String(params.supports_structured_output));
      if (params?.sort_by) queryParams.set('sort_by', params.sort_by);
      if (params?.offset !== undefined) queryParams.set('offset', String(params.offset));
      if (params?.limit !== undefined) queryParams.set('limit', String(params.limit));

      const queryStr = queryParams.toString();
      const endpoint = queryStr ? `/models?${queryStr}` : '/models';
      const data = await this.request<{ total: number; models: ModelProfile[] }>(endpoint);
      return { models: data.models, total: data.total };
    } catch {
      // Fallback to sample models if server not running
      return { models: SAMPLE_MODELS, total: SAMPLE_MODELS.length };
    }
  }

  async getModel(modelId: string): Promise<ModelProfile | null> {
    try {
      return await this.request<ModelProfile>(`/models/${encodeURIComponent(modelId)}`);
    } catch {
      return SAMPLE_MODELS.find((m) => m.id === modelId) || null;
    }
  }

  async refreshModels(): Promise<{ success: boolean; total_models: number }> {
    return this.request('/models/refresh', { method: 'POST' });
  }

  // Analytics Overview
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return this.request<AnalyticsOverview>('/analytics/overview');
  }

  // Verified Git Commit Analytics
  async getCommitAnalytics(): Promise<CommitAnalytics> {
    return this.request<CommitAnalytics>('/analytics/commits');
  }

  // Datasets
  async getDatasets(): Promise<DatasetItem[]> {
    try {
      const data = await this.request<{ items: DatasetItem[] }>('/datasets');
      return data.items || [];
    } catch {
      return [
        { id: 'coding_basics', name: 'Python Algorithmic Synthesis', description: 'Tests function generation, string reversal, and recursion.', version: 1, case_count: 3 },
        { id: 'structured_json', name: 'Constrained JSON Schema Extraction', description: 'Verifies typed schema extraction.', version: 1, case_count: 3 },
        { id: 'reasoning_math', name: 'Mathematical Word Logic', description: 'Multi-step algebraic word problems.', version: 1, case_count: 3 },
        { id: 'rag_retrieval', name: 'Needle-in-a-Haystack Fact Recall', description: 'Evaluates precision factual retrieval inside dense documents.', version: 1, case_count: 2 },
      ];
    }
  }

  // Evaluation Runs
  async getEvaluations(): Promise<EvaluationRun[]> {
    try {
      const data = await this.request<{ items: any[] }>('/evaluations');
      return (data.items || []).map((r) => ({
        id: r.id,
        model_id: r.model_id,
        model_name: r.name || r.model_id,
        benchmark_id: r.dataset_id || 'default',
        benchmark_name: r.dataset_name || 'Standard Benchmark Suite',
        status: r.status === 'completed' ? 'completed' : r.status === 'failed' ? 'failed' : 'running',
        is_demo: false,
        pass_rate: r.pass_rate || 0,
        passed_cases: r.passed_cases || 0,
        total_cases: r.total_cases || 0,
        avg_latency_ms: r.avg_latency_ms || 0,
        case_results: [],
        created_at: r.created_at,
      }));
    } catch {
      return [];
    }
  }

  async createEvaluation(payload: {
    model_id: string;
    provider?: string;
    dataset_id?: string;
    name?: string;
    temperature?: number;
    max_cases?: number;
  }): Promise<any> {
    return this.request('/evaluations', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getEvaluationDetails(id: string): Promise<any> {
    return this.request(`/evaluations/${id}`);
  }
}

export const api = new ApiService();
