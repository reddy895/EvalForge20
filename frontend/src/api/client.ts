import type {
  SystemHealthResponse,
  ReadinessResponse,
  RunSummary,
  RunDetailResponse,
  CaseResult,
  CreateEvaluationPayload,
  OllamaDiagnosticReport,
  DetailedModel,
  MetricDefinition,
  DatasetValidationReport,
  ComparisonResult,
  MultiRunComparisonMatrix,
} from './types';

export class ApiError extends Error {
  public status: number;
  public details?: any;

  constructor(message: string, status: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });

    if (!res.ok) {
      let errMsg = `Request failed with HTTP ${res.status}`;
      let errDetails: any = null;

      try {
        const errorJson = await res.json();
        errMsg = errorJson.message || errorJson.detail || errorJson.error || errMsg;
        errDetails = errorJson.details || errorJson;
      } catch {
        const text = await res.text().catch(() => '');
        if (text) errMsg = text;
      }

      throw new ApiError(errMsg, res.status, errDetails);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err?.message || 'Network error connecting to EvalForge20 backend',
      0,
      err
    );
  }
}

export const api = {
  // Health & Readiness
  getHealth: () => request<SystemHealthResponse>('/health'),
  getReadiness: () => request<ReadinessResponse>('/ready'),

  // Evaluation Runs
  listEvaluations: (params?: {
    limit?: number;
    offset?: number;
    status?: string;
    model_identifier?: string;
    min_pass_rate?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    if (params?.status) query.set('status', params.status);
    if (params?.model_identifier) query.set('model_identifier', params.model_identifier);
    if (params?.min_pass_rate !== undefined)
      query.set('min_pass_rate', String(params.min_pass_rate));

    const qs = query.toString();
    return request<RunSummary[]>(`/v1/evaluations${qs ? `?${qs}` : ''}`);
  },

  getEvaluation: (runId: string) => request<RunDetailResponse>(`/v1/evaluations/${runId}`),

  getCaseResults: (runId: string, limit = 50, offset = 0) =>
    request<CaseResult[]>(`/v1/evaluations/${runId}/results?limit=${limit}&offset=${offset}`),

  createEvaluation: (payload: CreateEvaluationPayload) =>
    request<RunSummary>('/v1/evaluations', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Reports
  getReportText: async (
    runId: string,
    format: 'json' | 'markdown' | 'csv' = 'json',
    redactInputs = false,
    redactOutputs = false
  ): Promise<string> => {
    const res = await fetch(
      `${API_BASE}/v1/reports/${runId}?format=${format}&redact_inputs=${redactInputs}&redact_outputs=${redactOutputs}`,
      { headers: { Accept: format === 'json' ? 'application/json' : 'text/plain' } }
    );
    if (!res.ok) {
      throw new ApiError(`Failed to export report: ${res.statusText}`, res.status);
    }
    return res.text();
  },

  // Comparisons
  compareRuns: (payload: {
    baseline_run_id: string;
    candidate_run_id: string;
    allow_different_datasets?: boolean;
  }) =>
    request<ComparisonResult>('/v1/compare', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  compareMatrix: (runIds: string[]) =>
    request<MultiRunComparisonMatrix>('/v1/compare/matrix', {
      method: 'POST',
      body: JSON.stringify({ run_ids: runIds }),
    }),

  // Ollama & Providers
  getOllamaStatus: () => request<OllamaDiagnosticReport>('/v1/ollama/status'),
  listModels: () => request<DetailedModel[]>('/v1/models'),
  listProviders: () => request<string[]>('/v1/providers'),

  // Evaluators & Metrics
  listMetrics: () => request<MetricDefinition[]>('/v1/metrics'),
  listEvaluators: () => request<MetricDefinition[]>('/v1/evaluators'),

  // Datasets
  validateDataset: (content: string) =>
    request<DatasetValidationReport>('/v1/datasets/validate', {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  listDatasets: () =>
    request<
      Array<{
        name: string;
        path: string;
        format: string;
        size_bytes: number;
        case_count: number;
      }>
    >('/v1/datasets'),

  // Integrations
  getLangSmithStatus: () => request<any>('/v1/integrations/langsmith/status'),
};
