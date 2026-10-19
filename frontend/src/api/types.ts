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
  providers_status?: Record<string, string>;
  langsmith_enabled: boolean;
}

export interface ModelPricing {
  input_price_per_m: number | null;
  output_price_per_m: number | null;
  cached_input_price_per_m?: number | null;
  currency: string;
  unit: string;
  effective_date: string;
  source_url: string;
  is_verified: boolean;
  notes?: string;
}

export interface CatalogModel {
  name: string;
  provider: string;
  model_identifier: string;
  is_local: boolean;
  context_window?: number | null;
  modalities: string[];
  supports_tools: boolean;
  supports_structured_output: boolean;
  release_date?: string | null;
  pricing?: ModelPricing | null;
  connection_status: 'online' | 'offline' | 'configured' | 'unconfigured' | 'unknown';
  description?: string;
}

export interface TaskCategoryMetrics {
  category: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number | null;
  failure_rate: number | null;
  mean_latency_ms: number | null;
  representative_failures?: Array<{
    case_id: string;
    input?: string;
    actual_output?: string;
    error_message?: string;
  }>;
}

export interface BandMetrics {
  band: 'low' | 'medium' | 'high' | 'unknown' | string;
  total_cases: number;
  passed_cases: number;
  pass_rate: number | null;
  mean_latency_ms: number | null;
  has_sufficient_data: boolean;
  insufficient_data_note?: string | null;
}

export interface RunAnalysisResponse {
  run_id: string;
  model_identifier: string;
  provider_name: string;
  total_cases: number;
  pass_rate: number | null;
  complexity_bands: Record<string, BandMetrics>;
  task_categories: TaskCategoryMetrics[];
  cost_breakdown?: {
    prompt_tokens?: number | null;
    completion_tokens?: number | null;
    total_tokens?: number | null;
    cloud_cost_usd?: number | null;
    total_estimated_cost_usd?: number | null;
    cost_per_successful_case_usd?: number | null;
    cost_per_1k_tasks_usd?: number | null;
    is_cost_known?: boolean;
    pricing_source?: string | null;
    assumptions?: string | null;
  };
}

export interface TaskCapabilityAnalysis {
  category: string;
  total_cases: number;
  pass_rate: number | null;
  mean_latency_ms: number | null;
  failure_rate: number;
  estimated_cost_per_task: number | null;
  representative_failures: Array<{
    case_id: string;
    input_preview: string;
    actual_output_preview?: string;
    error_message?: string;
  }>;
}

export interface ComplexityBandAnalysis {
  band: 'low' | 'medium' | 'high';
  case_count: number;
  pass_rate: number | null;
  mean_latency_ms: number | null;
  has_sufficient_data: boolean;
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
  /** True when Ollama daemon is reachable. Serialized from is_reachable field. */
  connected: boolean;
  /** Raw field — same as connected. Use connected for boolean checks. */
  is_reachable: boolean;
  base_url: string;
  version: string | null;
  /** Serialized alias for installed_models array. */
  models: string[];
  /** Installed model names. Same as models. */
  installed_models: string[];
  /** Count of installed models. */
  models_count: number;
  error_message: string | null;
  latency_ms: number | null;
  status_code: number | null;
  /** Status label: 'online' | 'no_models_installed' | 'offline' */
  status_label: 'online' | 'no_models_installed' | 'offline';
  setup_instructions: string[];
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

export interface MetricDelta {
  metric_id: string;
  baseline_value: number | null;
  candidate_value: number | null;
  delta: number | null;
  percentage_change: number | null;
}

export interface CaseRegression {
  case_id: string;
  baseline_passed: boolean | null;
  candidate_passed: boolean | null;
  reason: string;
}

export interface ComparisonResult {
  baseline_run_id: string;
  candidate_run_id: string;
  baseline_name?: string;
  candidate_name?: string;
  baseline_model?: string | null;
  candidate_model?: string | null;
  is_compatible?: boolean;
  dataset_version_hash?: string | null;
  metric_deltas?: Record<string, any>;
  pass_rate_delta?: number | null;
  score_delta?: number;
  mean_latency_delta_ms?: number | null;
  latency_delta_ms?: number;
  median_latency_delta_ms?: number | null;
  p95_latency_delta_ms?: number | null;
  cost_delta_usd?: number | null;
  regressed_cases?: CaseRegression[];
  improved_cases?: CaseRegression[];
  regressed_case_ids?: string[];
  improved_case_ids?: string[];
  regressions_detected?: boolean;
  threshold_violations?: string[];
  passed_regression_gate: boolean;
  disagreements?: Array<{
    case_id: string;
    baseline_passed: boolean;
    candidate_passed: boolean;
    baseline_output?: string;
    candidate_output?: string;
  }>;
  messages?: string[];
  summary?: string;
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
