/* EvalForge20 TypeScript API Definitions */

export interface SystemHealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface ReadinessResponse {
  status: string;
  database: string;
  version: string;
  environment: string;
  available_providers: string[];
  langsmith_enabled: boolean;
}

export interface TargetConfiguration {
  target_name: string;
  target_type: 'llm' | 'ollama' | 'rag' | 'agent' | 'mock';
  provider_name: string;
  model_identifier: string;
  base_url?: string | null;
  temperature: number;
  max_tokens?: number | null;
  timeout_seconds: number;
  extra_params?: Record<string, any>;
}

export interface EvaluatorConfiguration {
  evaluator_name: string;
  metric_id: string;
  weight?: number;
  threshold?: number | null;
  rubric_version?: string | null;
  options?: Record<string, any>;
}

export interface RunSummary {
  run_id: string;
  name: string;
  status: 'completed' | 'running' | 'failed' | 'queued' | string;
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  started_at: string | null;
  completed_at: string | null;
  pass_rate: number | null;
  error_message: string | null;
}

export interface AggregateMetrics {
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  pass_rate: number | null;
  mean_latency_ms: number | null;
  median_latency_ms: number | null;
  p95_latency_ms: number | null;
  total_tokens: number | null;
  metric_averages: Record<string, number>;
  metric_pass_rates: Record<string, number>;
  category_performance: Record<string, Record<string, number>>;
  error_distribution: Record<string, number>;
}

export interface MetricResult {
  metric_id: string;
  metric_name: string;
  score: number | null;
  passed: boolean | null;
  reason: string | null;
  details: Record<string, any>;
  is_model_based: boolean;
}

export interface CaseResult {
  case_id: string;
  run_id: string;
  input: string | Record<string, any>;
  actual_output: string | Record<string, any> | null;
  expected_output: string | Record<string, any> | null;
  metrics: MetricResult[];
  latency_ms: number | null;
  token_usage: Record<string, number> | null;
  error_category: string | null;
  error_message: string | null;
  trace: Record<string, any> | null;
}

export interface RunDetailResponse {
  run: {
    run_id: string;
    name: string;
    status: string;
    target_config_json?: string;
    evaluator_configs_json?: string;
    config: {
      target: TargetConfiguration;
      evaluators: EvaluatorConfiguration[];
      dataset_path?: string | null;
      dataset_version_hash?: string | null;
      max_concurrency: number;
      max_retries: number;
      timeout_seconds: number;
    };
    total_cases: number;
    completed_cases: number;
    failed_cases: number;
    started_at: string | null;
    completed_at: string | null;
    error_message: string | null;
  };
  aggregates: AggregateMetrics | null;
}

export interface CreateEvaluationPayload {
  name: string;
  dataset_path?: string | null;
  dataset_content?: string | null;
  target: TargetConfiguration;
  evaluators: EvaluatorConfiguration[];
  max_concurrency?: number;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface OllamaDiagnosticReport {
  connected: boolean;
  base_url: string;
  version: string | null;
  models_count: number;
  models: string[];
  error_message: string | null;
  latency_ms: number | null;
}

export interface DetailedModel {
  name: string;
  model: string;
  modified_at: string;
  size: number;
  digest: string;
  details?: {
    format?: string;
    family?: string;
    families?: string[];
    parameter_size?: string;
    quantization_level?: string;
  };
}

export interface MetricDefinition {
  metric_id: string;
  metric_name: string;
  description: string;
  category: 'deterministic' | 'model_based' | 'rag' | 'agent' | 'composite' | 'summary';
  requires_expected_output: boolean;
  valid_range: [number, number];
  options_schema: Record<string, any>;
}

export interface DatasetValidationIssue {
  line_number?: number | null;
  case_id?: string | null;
  severity: 'error' | 'warning';
  message: string;
}

export interface DatasetValidationReport {
  is_valid: boolean;
  total_lines_read: number;
  valid_cases_count: number;
  issues: DatasetValidationIssue[];
  dataset_hash?: string | null;
}

export interface ComparisonResult {
  baseline_run_id: string;
  candidate_run_id: string;
  baseline_name: string;
  candidate_name: string;
  passed_regression_gate: boolean;
  score_delta: number;
  latency_delta_ms: number;
  metric_deltas: Record<string, number>;
  regressed_case_ids: string[];
  improved_case_ids: string[];
  disagreements: Array<{
    case_id: string;
    baseline_passed: boolean;
    candidate_passed: boolean;
    baseline_output?: string;
    candidate_output?: string;
  }>;
  messages: string[];
}

export interface MultiRunComparisonMatrix {
  run_ids: string[];
  models: string[];
  runs_summary: Array<{
    run_id: string;
    name: string;
    model: string;
    pass_rate: number | null;
    mean_latency_ms: number | null;
    total_cases: number;
  }>;
  common_case_ids: string[];
  metrics_comparison: Record<string, Record<string, number>>;
}
