/**
 * Frontend evaluation and benchmark TypeScript definitions.
 */

export interface TestCaseResultItem {
  case_id: string;
  prompt: string;
  expected_output: string;
  actual_output: string;
  passed: boolean;
  latency_ms: number;
}

export interface EvaluationJobSummary {
  id: string;
  model_id: string;
  model_name: string;
  benchmark_name: string;
  pass_rate: number;
  total_cases: number;
  passed_cases: number;
  avg_latency_ms: number;
  status: 'completed' | 'failed' | 'running';
  created_at: string;
}
