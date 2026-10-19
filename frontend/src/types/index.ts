/**
 * Core domain types for EvalForge20 frontend.
 */

export interface BenchmarkResult {
  benchmark_name: string;
  metric: string;
  score: number;
  sample_size?: number | null;
  date_evaluated?: string | null;
  source: string;
  is_local_measurement?: boolean;
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

export interface ModelSummary {
  id: string;
  name: string;
  provider: string;
  model_identifier: string;
  family: string;
  parameter_count?: string | null;
  context_window: number;
  is_local: boolean;
  is_installed: boolean;
  supports_tools: boolean;
  supports_structured_output: boolean;
  license: string;
  hardware_min_ram_gb: number;
  recommended_tasks: string[];
  headline_benchmark_score?: number | null;
  headline_benchmark_name?: string | null;
  pricing_summary: string;
}

export type ModelCatalogItem = ModelSummary;

export interface ModelProfile {
  id: string;
  name: string;
  provider: string;
  model_identifier: string;
  family: string;
  architecture?: string | null;
  parameter_count?: string | null;
  size_bytes?: number | null;
  quantization?: string | null;
  context_window: number;
  modalities: string[];
  supports_tools: boolean;
  supports_structured_output: boolean;
  license: string;
  is_commercial_use_allowed: boolean;
  release_date?: string | null;
  description: string;
  is_local: boolean;
  is_installed: boolean;
  benchmarks: BenchmarkResult[];
  measured_latency_ms?: number | null;
  measured_throughput_tok_s?: number | null;
  pricing?: ModelPricing | null;
  hardware: HardwareRequirements;
  strengths: string[];
  weaknesses: string[];
  recommended_tasks: string[];
  unsuitable_tasks: string[];
}

export interface OllamaModel {
  name: string;
  size?: number;
  digest?: string;
  modified_at?: string;
}

export interface OllamaStatus {
  online: boolean;
  models: OllamaModel[];
  base_url: string;
  error?: string | null;
}

export interface OllamaStatusReport {
  is_reachable: boolean;
  base_url: string;
  version?: string | null;
  installed_models: string[];
  models_count: number;
  status_label: 'online' | 'no_models_installed' | 'offline';
  latency_ms?: number | null;
  error_message?: string | null;
  setup_instructions: string[];
}

export interface BenchmarkDefinition {
  id: string;
  name: string;
  task: string;
  description: string;
  total_cases: number;
}

export type BenchmarkTask = BenchmarkDefinition;

export interface EvaluationCaseResult {
  case_id: string;
  prompt: string;
  expected_output?: string | null;
  actual_output?: string | null;
  passed: boolean;
  latency_ms: number;
  error?: string | null;
}

export interface EvaluationRunMetrics {
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number;
  avg_latency_ms: number;
}

export interface EvaluationRun {
  id: string;
  model_id: string;
  benchmark_id: string;
  benchmark_name: string;
  status: string;
  metrics: EvaluationRunMetrics;
  case_results: EvaluationCaseResult[];
  created_at: string;
}

export interface CaseMetricResult {
  metric_name: string;
  passed: boolean;
  score: number;
  details?: string | null;
}

export interface CaseResult {
  case_id: string;
  prompt: string;
  expected_output?: string | null;
  actual_output?: string | null;
  passed: boolean;
  latency_ms: number;
  error_message?: string | null;
  error_category?: string | null;
  metrics: CaseMetricResult[];
}

export interface AggregateMetrics {
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  pass_rate?: number | null;
  mean_latency_ms?: number | null;
  p95_latency_ms?: number | null;
  total_tokens?: number | null;
  metric_averages: Record<string, number>;
  error_distribution: Record<string, number>;
}

export interface EvaluationRunSummary {
  id: string;
  name: string;
  model_identifier: string;
  provider: string;
  task_id: string;
  status: string;
  total_cases: number;
  completed_cases: number;
  pass_rate?: number | null;
  mean_latency_ms?: number | null;
  created_at: string;
  completed_at?: string | null;
}

export interface EvaluationRunDetail {
  id: string;
  name: string;
  model_identifier: string;
  provider: string;
  task_id: string;
  status: string;
  total_cases: number;
  completed_cases: number;
  pass_rate?: number | null;
  aggregates: AggregateMetrics;
  case_results: CaseResult[];
  created_at: string;
  completed_at?: string | null;
}

export interface ModelRecommendation {
  model_id: string;
  model_name: string;
  provider: string;
  match_score: number;
  is_local: boolean;
  is_installed: boolean;
  hardware_fit: string;
  recommendation_reason: string;
  key_evidence: string[];
  important_tradeoffs: string[];
  evidence_source: string;
}

export interface TaskRecommendationResponse {
  task: string;
  evaluated_criteria: string[];
  recommendations: ModelRecommendation[];
  explanation: string;
}

export interface ComparisonRow {
  metric_name: string;
  category: string;
  values: Record<string, string | number | boolean | null>;
  winner_model_id?: string | null;
  note?: string | null;
}

export interface ModelComparisonResult {
  compared_models: { id: string; name: string; provider: string }[];
  matrix: ComparisonRow[];
  summary_verdict: string;
  comparability_notes: string[];
}

export interface HardwareProfile {
  os: string;
  ram_gb: number;
  vram_gb: number;
  gpu_name: string;
  cpu_cores: number;
  disk_available_gb: number;
}

export type NavRoute = 'landing' | 'models' | 'model-detail' | 'compare' | 'evaluate' | 'history';

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
  onlyLocal: boolean;
  sortBy: 'recommended' | 'benchmark' | 'context' | 'ram';
}

export interface DemoEvaluationState {
  modelId: string;
  taskId: string;
  benchmarkId: string;
  sampleCount: number;
  isRunning: boolean;
  stepProgress: number;
  currentStepDescription: string;
  result: EvaluationRun | null;
}

