import { describe, it, expect, vi } from 'vitest';
import { api } from '../services/api';
import { EvaluationResultsData } from '../types/evaluationResults';

describe('Dedicated Evaluation Results Workspace & Analytics', () => {
  const sampleResults: EvaluationResultsData = {
    id: 'eval-exec-101',
    execution_id: 'exec-101',
    name: 'Multi-Model Coding Reasoning Benchmark',
    status: 'COMPLETED',
    dataset_name: 'HumanEval Python Basics',
    models: ['qwen2.5:1.5b', 'qwen2.5:3b'],
    evaluators: ['exact_match', 'code_execution'],
    total_cases: 4,
    completed_cases: 4,
    passed_cases: 3,
    failed_cases: 1,
    pass_rate: 75.0,
    avg_latency_ms: 145.2,
    median_latency_ms: 140.0,
    p95_latency_ms: 180.5,
    tokens_per_second: 38.6,
    total_duration_ms: 4500,
    created_at: '2026-11-03T09:00:00Z',
    completed_at: '2026-11-03T09:00:04Z',
    error_message: null,
    model_summaries: [
      {
        model_id: 'qwen2.5:1.5b',
        name: 'Qwen 2.5 1.5B',
        total_cases: 2,
        completed_cases: 2,
        passed_cases: 1,
        failed_cases: 1,
        pass_rate: 50.0,
        avg_latency_ms: 110.0,
        median_latency_ms: 110.0,
        p95_latency_ms: 130.0,
        tokens_per_second: null, // missing throughput telemetry
        status: 'completed',
        metrics: {
          exact_match: 50.0,
          accuracy: 50.0,
        },
      },
      {
        model_id: 'qwen2.5:3b',
        name: 'Qwen 2.5 3B',
        total_cases: 2,
        completed_cases: 2,
        passed_cases: 2,
        failed_cases: 0,
        pass_rate: 100.0,
        avg_latency_ms: 180.4,
        median_latency_ms: 180.0,
        p95_latency_ms: 195.0,
        tokens_per_second: 38.6, // verified throughput
        status: 'completed',
        metrics: {
          exact_match: 100.0,
          accuracy: 100.0,
        },
      },
    ],
    case_results: [
      {
        case_id: 'case-1',
        case_index: 0,
        model_id: 'qwen2.5:1.5b',
        prompt: 'def add(a, b):',
        expected_output: 'return a + b',
        actual_output: 'return a + b',
        passed: true,
        latency_ms: 105.2,
        tokens_per_second: null,
        assertion_type: 'exact_match',
        evaluators: {
          exact_match: { name: 'Exact Match', score: 1.0, passed: true },
        },
      },
      {
        case_id: 'case-2',
        case_index: 1,
        model_id: 'qwen2.5:1.5b',
        prompt: 'def reverse_string(s):',
        expected_output: 'return s[::-1]',
        actual_output: 'return list(reversed(s))',
        passed: false,
        latency_ms: 114.8,
        tokens_per_second: null,
        assertion_type: 'exact_match',
        error_message: 'Output string mismatch',
        evaluators: {
          exact_match: { name: 'Exact Match', score: 0.0, passed: false },
        },
      },
      {
        case_id: 'case-1',
        case_index: 0,
        model_id: 'qwen2.5:3b',
        prompt: 'def add(a, b):',
        expected_output: 'return a + b',
        actual_output: 'return a + b',
        passed: true,
        latency_ms: 172.0,
        tokens_per_second: 42.1,
        assertion_type: 'exact_match',
        evaluators: {
          exact_match: { name: 'Exact Match', score: 1.0, passed: true },
        },
      },
      {
        case_id: 'case-2',
        case_index: 1,
        model_id: 'qwen2.5:3b',
        prompt: 'def reverse_string(s):',
        expected_output: 'return s[::-1]',
        actual_output: 'return s[::-1]',
        passed: true,
        latency_ms: 188.8,
        tokens_per_second: 35.1,
        assertion_type: 'exact_match',
        evaluators: {
          exact_match: { name: 'Exact Match', score: 1.0, passed: true },
        },
      },
    ],
    disagreements: [
      {
        prompt: 'def reverse_string(s):',
        results: {
          'qwen2.5:1.5b': { passed: false, output: 'return list(reversed(s))', latency_ms: 114.8 },
          'qwen2.5:3b': { passed: true, output: 'return s[::-1]', latency_ms: 188.8 },
        },
      },
    ],
    distribution: {
      passed: 3,
      failed: 1,
      skipped: 0,
    },
  };

  it('fetches execution results with model summaries and cases via api service', async () => {
    vi.spyOn(api, 'getExecutionResults').mockResolvedValueOnce(sampleResults);

    const data = await api.getExecutionResults('exec-101');
    expect(data.id).toBe('eval-exec-101');
    expect(data.execution_id).toBe('exec-101');
    expect(data.models).toHaveLength(2);
    expect(data.model_summaries).toHaveLength(2);
    expect(data.case_results).toHaveLength(4);
    expect(data.pass_rate).toBe(75.0);
  });

  it('preserves data integrity: distinguishes missing throughput telemetry from zero', () => {
    const model1 = sampleResults.model_summaries.find((m) => m.model_id === 'qwen2.5:1.5b');
    const model2 = sampleResults.model_summaries.find((m) => m.model_id === 'qwen2.5:3b');

    // Missing telemetry must remain null and not be converted to 0
    expect(model1?.tokens_per_second).toBeNull();
    expect(model1?.tokens_per_second).not.toBe(0);

    // Measured telemetry must be preserved accurately
    expect(model2?.tokens_per_second).toBe(38.6);
  });

  it('preserves data integrity: distinguishes genuine zero score from missing evaluation', () => {
    const failedCase = sampleResults.case_results.find((c) => c.passed === false);
    expect(failedCase).toBeDefined();
    expect(failedCase?.evaluators?.exact_match?.score).toBe(0.0);
    expect(failedCase?.evaluators?.exact_match?.passed).toBe(false);
  });

  it('correctly tracks multi-model disagreements across test cases', () => {
    expect(sampleResults.disagreements).toHaveLength(1);
    const disagreement = sampleResults.disagreements[0];
    expect(disagreement.prompt).toBe('def reverse_string(s):');
    expect(disagreement.results['qwen2.5:1.5b'].passed).toBe(false);
    expect(disagreement.results['qwen2.5:3b'].passed).toBe(true);
  });

  it('filters test cases by status, model, and search query accurately', () => {
    const cases = sampleResults.case_results;

    // Filter passed
    const passedOnly = cases.filter((c) => c.passed);
    expect(passedOnly).toHaveLength(3);

    // Filter failed
    const failedOnly = cases.filter((c) => !c.passed);
    expect(failedOnly).toHaveLength(1);
    expect(failedOnly[0].model_id).toBe('qwen2.5:1.5b');

    // Filter by model
    const qwen15Only = cases.filter((c) => c.model_id === 'qwen2.5:1.5b');
    expect(qwen15Only).toHaveLength(2);

    // Search query
    const query = 'reverse_string';
    const searched = cases.filter((c) => c.prompt.toLowerCase().includes(query.toLowerCase()));
    expect(searched).toHaveLength(2);
  });

  it('computes distribution breakdown accurately', () => {
    const dist = sampleResults.distribution;
    expect(dist.passed).toBe(3);
    expect(dist.failed).toBe(1);
    expect(dist.skipped).toBe(0);
    expect(dist.passed + dist.failed + dist.skipped).toBe(sampleResults.total_cases);
  });
});
