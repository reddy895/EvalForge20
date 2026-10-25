/**
 * EvalForge20 Core Types
 */

export interface BenchmarkScore {
  benchmark_name: string;
  metric: string;
  score: number;
  source: string;
  verified: boolean;
}

export interface HardwareRequirements {
  min_ram_gb: number;
  recommended_ram_gb: number;
  min_vram_gb?: number | null;
  quantization: string;
  context_length: number;
  disk_space_gb: number;
}

export interface ModelPricing {
  input_cost_per_m?: number | null;
  output_cost_per_m?: number | null;
  currency: string;
  unit: string;
  is_free_local: boolean;
  source_url?: string | null;
}

export interface ModelProfile {
  id: string;
  name: string;
  provider: string;
  model_identifier: string;
  family: string;
  architecture: string;
  parameter_count: string;
  quantization?: string;
  context_window: number;
  modalities: string[];
  supports_tools: boolean;
  supports_structured_output: boolean;
  license: string;
  is_commercial_use_allowed: boolean;
  release_date: string;
  description: string;
  is_local: boolean;
  is_installed: boolean;
  benchmarks: BenchmarkScore[];
  measured_latency_ms?: number | null;
  measured_throughput_tok_s?: number | null;
  pricing: ModelPricing;
  hardware: HardwareRequirements;
  strengths: string[];
  weaknesses: string[];
  recommended_tasks: string[];
  unsuitable_tasks: string[];
}

export interface ModelSummary {
  id: string;
  name: string;
  provider: string;
  model_identifier: string;
  family: string;
  parameter_count: string;
  context_window: number;
  is_local: boolean;
  is_installed: boolean;
  supports_tools: boolean;
  supports_structured_output: boolean;
  license: string;
  hardware_min_ram_gb: number;
  recommended_tasks: string[];
  headline_benchmark_score: number | null;
  headline_benchmark_name: string | null;
  pricing_summary: string;
  description: string;
}

export interface BenchmarkDefinition {
  id: string;
  name: string;
  task: string;
  description: string;
  total_cases: number;
}

export interface TestCaseResult {
  case_id: string;
  prompt: string;
  expected_output: string;
  actual_output: string;
  passed: boolean;
  latency_ms?: number | null;
  assertion_type: string;
}

export interface EvaluationRun {
  id: string;
  model_id: string;
  model_name: string;
  benchmark_id: string;
  benchmark_name: string;
  status: 'idle' | 'queued' | 'running' | 'completed' | 'completed_with_errors' | 'failed' | 'cancelled';
  is_demo: boolean;
  pass_rate: number | null;
  passed_cases: number;
  total_cases: number;
  avg_latency_ms?: number;
  median_latency_ms?: number;
  p95_latency_ms?: number;
  tokens_per_second?: number;
  load_duration_ms?: number;
  eval_duration_ms?: number;
  total_tokens?: number;
  case_results: TestCaseResult[];
  created_at: string;
  error_message?: string;
}

export type NavRoute = 'landing' | 'models' | 'model-detail' | 'compare' | 'evaluate' | 'history' | 'analytics';

export type LandingSectionId =
  | 'hero'
  | 'discovery'
  | 'why'
  | 'how-it-works'
  | 'comparison'
  | 'evaluation'
  | 'local-first'
  | 'cta';

export interface FilterOptions {
  query: string;
  provider: string;
  task: string;
  onlyInstalled: boolean;
  sortBy: 'recommended' | 'benchmark' | 'context' | 'ram';
}

export interface ProviderDetail {
  name: string;
  display_name: string;
  provider_type: 'local' | 'cloud';
  implementation_status: 'implemented_and_tested' | 'configurable_cloud' | 'planned';
  healthy: boolean;
  is_configured: boolean;
  default: boolean;
  base_url?: string | null;
  setup_instructions?: string | null;
  supported_models_count: number;
}

export interface CommitItem {
  hash: string;
  date: string;
  author: string;
  message: string;
}

export interface DailyCommitActivity {
  date: string;
  count: number;
  level: number;
  sample_commits: CommitItem[];
}

export interface CommitAnalytics {
  target_commits: number;
  total_verified_commits: number;
  target_achieved: boolean;
  target_progress_percent: number;
  status_label: string;
  source: string;
  time_range_start: string;
  time_range_end: string;
  author_distribution: Record<string, number>;
  daily_activity: DailyCommitActivity[];
  last_updated: string;
}

export interface AnalyticsOverview {
  total_providers: number;
  healthy_providers: number;
  total_models: number;
  local_models_count: number;
  cloud_models_count: number;
  total_evaluation_runs: number;
  completed_runs: number;
  failed_runs: number;
  running_runs: number;
  cancelled_runs: number;
  overall_pass_rate_percent: number;
  overall_reliability_percent: number;
  average_latency_ms: number;
  total_test_cases_evaluated: number;
  total_benchmark_comparisons: number;
  total_agent_evaluations: number;
  recent_runs: Array<{
    id: string;
    name: string;
    model_id: string;
    provider: string;
    dataset_name?: string;
    status: string;
    pass_rate?: number;
    avg_latency_ms?: number;
    total_cases?: number;
    passed_cases?: number;
    created_at: string;
  }>;
  model_scorecards: Array<{
    model_id: string;
    total_runs: number;
    avg_pass_rate: number;
    avg_latency_ms: number;
  }>;
  timestamp: string;
}

export interface DatasetItem {
  id: string;
  name: string;
  description?: string;
  version: number;
  case_count?: number;
  created_at?: string;
}

export interface LatencyDistribution {
  model_id: string;
  model_name: string;
  sample_count: number;
  mean_ms: number;
  min_ms: number;
  p10_ms: number;
  p25_ms: number;
  p50_ms: number;
  p75_ms: number;
  p90_ms: number;
  p95_ms: number;
  p99_ms: number;
  max_ms: number;
  raw_samples: number[];
}

