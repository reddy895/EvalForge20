/**
 * Comprehensive TypeScript types for the dedicated Evaluation Results workspace.
 */

export interface ModelSummary {
  model_id: string;
  name: string;
  total_cases: number;
  completed_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number; // percentage 0 - 100
  avg_latency_ms: number | null;
  median_latency_ms?: number | null;
  p95_latency_ms?: number | null;
  tokens_per_second?: number | null;
  status: string;
  metrics: Record<string, number | null | undefined>;
}

export interface EvaluatorScoreDetail {
  name?: string;
  score?: number | null;
  passed?: boolean;
  method?: string;
  details?: Record<string, unknown>;
}

export interface TestCaseResult {
  case_id: string;
  case_index?: number;
  model_id: string;
  prompt: string;
  expected_output?: string | null;
  actual_output?: string | null;
  passed: boolean;
  latency_ms?: number | null;
  tokens_per_second?: number | null;
  assertion_type?: string;
  evaluators?: Record<string, EvaluatorScoreDetail>;
  metrics?: Record<string, unknown>;
  error_message?: string | null;
  created_at?: string;
}

export interface DisagreementResult {
  passed?: boolean;
  output?: string;
  latency_ms?: number;
}

export interface DisagreementItem {
  prompt: string;
  results: Record<string, DisagreementResult>;
}

export interface EvaluationDistribution {
  passed: number;
  failed: number;
  skipped: number;
}

export interface EvaluationResultsData {
  id: string;
  execution_id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | string;
  dataset_name: string;
  models: string[];
  evaluators: string[];
  total_cases: number;
  completed_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number;
  avg_latency_ms: number | null;
  median_latency_ms?: number | null;
  p95_latency_ms?: number | null;
  tokens_per_second?: number | null;
  total_duration_ms?: number | null;
  created_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  model_summaries: ModelSummary[];
  case_results: TestCaseResult[];
  disagreements: DisagreementItem[];
  distribution: EvaluationDistribution;
}

export interface LiveExecutionProgress {
  stage: string;
  current_model?: string | null;
  current_evaluator?: string | null;
  completed_steps: number;
  total_steps: number;
  progress_percentage: number;
  elapsed_time_seconds: number;
  logs: string[];
  error?: string | null;
}

