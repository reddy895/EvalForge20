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
  latency_ms: number;
  assertion_type: string;
}

export interface EvaluationRun {
  id: string;
  model_id: string;
  model_name: string;
  benchmark_id: string;
  benchmark_name: string;
  status: 'completed' | 'failed' | 'running';
  is_demo: boolean;
  pass_rate: number;
  passed_cases: number;
  total_cases: number;
  avg_latency_ms: number;
  case_results: TestCaseResult[];
  created_at: string;
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
  onlyInstalled: boolean;
  sortBy: 'recommended' | 'benchmark' | 'context' | 'ram';
}
