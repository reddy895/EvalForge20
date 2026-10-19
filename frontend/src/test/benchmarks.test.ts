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
});
