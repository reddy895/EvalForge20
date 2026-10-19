/**
 * Centralized API client service talking directly to the FastAPI backend.
 */
import type {
  ModelSummary,
  ModelProfile,
  OllamaStatusReport,
  OllamaStatus,
  BenchmarkTask,
  EvaluationRunSummary,
  EvaluationRunDetail,
  EvaluationRun,
  TaskRecommendationResponse,
  ModelComparisonResult,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let errMsg = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      errMsg = errJson.message || errJson.detail || errJson.error || errMsg;
    } catch {
      const txt = await res.text().catch(() => '');
      if (txt) errMsg = txt;
    }
    throw new Error(errMsg);
  }

  return (await res.json()) as T;
}

export const api = {
  // Models Catalog
  listModels: (params?: {
    query?: string;
    provider?: string;
    task?: string;
    is_local?: boolean;
    is_installed?: boolean;
    sort_by?: string;
  }): Promise<ModelSummary[]> => {
    const qs = new URLSearchParams();
    if (params?.query) qs.set('query', params.query);
    if (params?.provider) qs.set('provider', params.provider);
    if (params?.task) qs.set('task', params.task);
    if (params?.is_local !== undefined) qs.set('is_local', String(params.is_local));
    if (params?.is_installed !== undefined) qs.set('is_installed', String(params.is_installed));
    if (params?.sort_by) qs.set('sort_by', params.sort_by);
    return request<ModelSummary[]>(`/v1/models${qs.toString() ? `?${qs.toString()}` : ''}`);
  },

  getModels: (params?: {
    query?: string;
    provider?: string;
    task?: string;
    is_local?: boolean;
    is_installed?: boolean;
    sort_by?: string;
  }): Promise<ModelSummary[]> => {
    return api.listModels(params);
  },

  getModelProfile: (modelId: string): Promise<ModelProfile> => {
    return request<ModelProfile>(`/v1/models/${encodeURIComponent(modelId)}`);
  },

  // Ollama Daemon
  getOllamaStatus: async (): Promise<OllamaStatus> => {
    try {
      const report = await request<OllamaStatusReport>('/v1/ollama/status');
      return {
        online: report.is_reachable,
        base_url: report.base_url,
        models: report.installed_models.map((name) => ({ name })),
        error: report.error_message,
      };
    } catch (err: any) {
      return {
        online: false,
        base_url: 'http://localhost:11434',
        models: [],
        error: err.message,
      };
    }
  },

  getOllamaReport: (): Promise<OllamaStatusReport> => {
    return request<OllamaStatusReport>('/v1/ollama/status');
  },

  pullOllamaModel: (model: string): Promise<{ model: string; status: string; message: string }> => {
    return request('/v1/ollama/pull', {
      method: 'POST',
      body: JSON.stringify({ model }),
    });
  },

  // Benchmarks & Evaluations
  listBenchmarks: (): Promise<BenchmarkTask[]> => {
    return request<BenchmarkTask[]>('/v1/benchmarks');
  },

  getBenchmarks: (): Promise<BenchmarkTask[]> => {
    return api.listBenchmarks();
  },

  createEvaluation: (payload: {
    name: string;
    model_identifier: string;
    provider?: string;
    task_id: string;
    max_cases?: number;
    temperature?: number;
  }): Promise<EvaluationRunDetail> => {
    return request<EvaluationRunDetail>('/v1/evaluations', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  runEvaluation: async (params: {
    model_id: string;
    benchmark_id: string;
    limit?: number;
  }): Promise<EvaluationRun> => {
    const detail = await api.createEvaluation({
      name: `Eval ${params.model_id} on ${params.benchmark_id}`,
      model_identifier: params.model_id,
      task_id: params.benchmark_id,
      max_cases: params.limit || 3,
      provider: params.model_id.includes('mock') ? 'mock' : 'ollama',
    });

    return {
      id: detail.id,
      model_id: detail.model_identifier,
      benchmark_id: detail.task_id,
      benchmark_name: detail.name,
      status: detail.status,
      metrics: {
        total_cases: detail.aggregates.total_cases,
        passed_cases: detail.aggregates.completed_cases,
        failed_cases: detail.aggregates.failed_cases,
        pass_rate: detail.aggregates.pass_rate || 0,
        avg_latency_ms: detail.aggregates.mean_latency_ms || 0,
      },
      case_results: detail.case_results.map((c: any) => ({
        case_id: c.case_id,
        prompt: c.prompt,
        expected_output: c.expected_output,
        actual_output: c.actual_output,
        passed: c.passed,
        latency_ms: c.latency_ms,
        error: c.error_message,
      })),
      created_at: detail.created_at,
    };
  },

  listEvaluations: (limit = 50, offset = 0): Promise<EvaluationRunSummary[]> => {
    return request<EvaluationRunSummary[]>(`/v1/evaluations?limit=${limit}&offset=${offset}`);
  },

  getEvaluationRuns: async (): Promise<EvaluationRun[]> => {
    const summaries = await api.listEvaluations(50, 0);
    // Fetch details for historical runs
    const runs: EvaluationRun[] = [];
    for (const s of summaries.slice(0, 15)) {
      try {
        const d = await api.getEvaluationDetail(s.id);
        runs.push({
          id: d.id,
          model_id: d.model_identifier,
          benchmark_id: d.task_id,
          benchmark_name: d.name,
          status: d.status,
          metrics: {
            total_cases: d.aggregates.total_cases,
            passed_cases: d.aggregates.completed_cases,
            failed_cases: d.aggregates.failed_cases,
            pass_rate: d.aggregates.pass_rate || 0,
            avg_latency_ms: d.aggregates.mean_latency_ms || 0,
          },
          case_results: d.case_results.map((c: any) => ({
            case_id: c.case_id,
            prompt: c.prompt,
            expected_output: c.expected_output,
            actual_output: c.actual_output,
            passed: c.passed,
            latency_ms: c.latency_ms,
            error: c.error_message,
          })),
          created_at: d.created_at,
        });
      } catch {
        // ignore individual failed fetches
      }
    }
    return runs;
  },

  getEvaluationDetail: (runId: string): Promise<EvaluationRunDetail> => {
    return request<EvaluationRunDetail>(`/v1/evaluations/${runId}`);
  },

  // Recommendations & Comparisons
  getTaskRecommendations: (task: string, preferLocal = true, maxRamGb?: number): Promise<TaskRecommendationResponse> => {
    return request<TaskRecommendationResponse>('/v1/recommendations/task', {
      method: 'POST',
      body: JSON.stringify({
        task,
        prefer_local: preferLocal,
        max_ram_gb: maxRamGb,
      }),
    });
  },

  compareModels: (modelIds: string[]): Promise<ModelComparisonResult> => {
    return request<ModelComparisonResult>('/v1/comparisons', {
      method: 'POST',
      body: JSON.stringify({ model_ids: modelIds }),
    });
  },

  // Health
  getHealth: (): Promise<{ status: string; app: string; version: string }> => {
    return request('/health');
  },
};

export const apiClient = api;
