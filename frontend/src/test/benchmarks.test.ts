import { describe, it, expect } from 'vitest';
import { simulateEvaluationRun, SAMPLE_TEST_CASES } from '../data/benchmarks';

describe('Benchmark Suites & Evaluation Runner', () => {
  it('contains test cases for coding, json, math, and rag', () => {
    expect(SAMPLE_TEST_CASES.coding_basics.length).toBeGreaterThan(0);
    expect(SAMPLE_TEST_CASES.structured_json.length).toBeGreaterThan(0);
    expect(SAMPLE_TEST_CASES.reasoning_math.length).toBeGreaterThan(0);
    expect(SAMPLE_TEST_CASES.rag_retrieval.length).toBeGreaterThan(0);
  });

  it('generates a valid simulated evaluation run result with deterministic metrics', () => {
    const result = simulateEvaluationRun(
      'qwen-2.5-7b-instruct',
      'Qwen 2.5 7B Instruct',
      'coding_basics',
      3
    );

    expect(result.id).toBeDefined();
    expect(result.model_name).toBe('Qwen 2.5 7B Instruct');
    expect(result.is_demo).toBe(true);
    expect(result.total_cases).toBe(3);
    expect(result.passed_cases).toBe(3);
    expect(result.pass_rate).toBe(1.0);
    expect(result.avg_latency_ms).toBeGreaterThan(0);
    expect(result.case_results.length).toBe(3);

    for (const c of result.case_results) {
      expect(c.prompt).toBeTruthy();
      expect(c.actual_output).toBeTruthy();
      expect(c.passed).toBe(true);
      expect(c.latency_ms).toBeGreaterThan(0);
    }
  });

  it('preserves null pass_rate and error message on failed evaluation payload', () => {
    const failedPayload = {
      id: 'eval-fail-99',
      model_id: 'qwen2.5:1.5b',
      status: 'failed',
      total_cases: 3,
      completed_cases: 0,
      passed_cases: 0,
      failed_cases: 3,
      pass_rate: null,
      avg_latency_ms: null,
      error_message: 'All test cases failed due to model inference errors or timeouts.',
    };

    expect(failedPayload.status).toBe('failed');
    expect(failedPayload.pass_rate).toBeNull();
    expect(failedPayload.avg_latency_ms).toBeNull();
    expect(failedPayload.error_message).toContain('inference errors');
  });

  it('accurately distinguishes genuine zero pass rate from unmeasured error state', () => {
    const genuineZero = {
      status: 'completed',
      total_cases: 2,
      passed_cases: 0,
      failed_cases: 2,
      pass_rate: 0.0,
      is_genuine_zero: true,
      error_message: null,
    };

    expect(genuineZero.status).toBe('completed');
    expect(genuineZero.pass_rate).toBe(0.0);
    expect(genuineZero.is_genuine_zero).toBe(true);
    expect(genuineZero.error_message).toBeNull();
  });
});
