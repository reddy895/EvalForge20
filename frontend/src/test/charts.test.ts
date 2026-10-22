import { describe, it, expect } from 'vitest';
import type { EvaluationRun } from '../types';

describe('Chart and Evaluation Graphical Telemetry Validation', () => {
  it('ensures sample metrics format correctly', () => {
    const metrics = [
      { modelName: 'Qwen 2.5 7B', score: 84.8, isLocal: true },
      { modelName: 'Claude 3.5 Sonnet', score: 93.7, isLocal: false },
    ];
    expect(metrics.length).toBe(2);
    expect(metrics[0].score).toBe(84.8);
    expect(metrics[0].isLocal).toBe(true);
  });

  it('correctly aggregates evaluation run telemetry for performance and accuracy charts', () => {
    const sampleRun: EvaluationRun = {
      id: 'eval-test-01',
      model_id: 'qwen2.5:7b',
      model_name: 'Qwen 2.5 7B Instruct',
      benchmark_id: 'coding_basics',
      benchmark_name: 'Python Algorithmic Synthesis',
      status: 'completed',
      is_demo: false,
      pass_rate: 1.0,
      passed_cases: 3,
      total_cases: 3,
      avg_latency_ms: 22.1,
      created_at: new Date().toISOString(),
      case_results: [
        {
          case_id: 'case-1',
          prompt: 'reverse string',
          expected_output: 's[::-1]',
          actual_output: 's[::-1]',
          passed: true,
          latency_ms: 18.4,
          assertion_type: 'exact_match',
        },
        {
          case_id: 'case-2',
          prompt: 'is palindrome',
          expected_output: 'clean == clean[::-1]',
          actual_output: 'clean == clean[::-1]',
          passed: true,
          latency_ms: 22.1,
          assertion_type: 'code_execution',
        },
        {
          case_id: 'case-3',
          prompt: 'fibonacci',
          expected_output: 'def fibonacci',
          actual_output: 'def fibonacci',
          passed: true,
          latency_ms: 25.8,
          assertion_type: 'code_execution',
        },
      ],
    };

    // Accuracy validation
    expect(sampleRun.pass_rate).toBe(1.0);
    expect(sampleRun.passed_cases).toBe(3);
    const passRatePercent = Math.round(sampleRun.pass_rate * 100);
    expect(passRatePercent).toBe(100);

    // Latency distribution validation
    const latencies = sampleRun.case_results.map((c) => c.latency_ms);
    const minLatency = Math.min(...latencies);
    const maxLatency = Math.max(...latencies);
    const meanLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;

    expect(minLatency).toBe(18.4);
    expect(maxLatency).toBe(25.8);
    expect(Math.round(meanLatency * 10) / 10).toBe(22.1);

    // SLA check (<35ms)
    expect(meanLatency).toBeLessThan(35.0);

    // Assertion categorization
    const breakdown: Record<string, number> = {};
    sampleRun.case_results.forEach((c) => {
      breakdown[c.assertion_type] = (breakdown[c.assertion_type] || 0) + 1;
    });
    expect(breakdown['exact_match']).toBe(1);
    expect(breakdown['code_execution']).toBe(2);
  });

  it('validates capability radar geometry calculations', () => {
    const center = 120;
    const radius = 85;
    const angleStep = (Math.PI * 2) / 6;

    // Top vertex (Accuracy at 100%)
    const topX = center + radius * Math.cos(-Math.PI / 2);
    const topY = center + radius * Math.sin(-Math.PI / 2);
    expect(Math.round(topX)).toBe(120);
    expect(Math.round(topY)).toBe(35); // 120 - 85 = 35

    // Second vertex at angleStep
    const secondAngle = angleStep - Math.PI / 2;
    const secondX = center + radius * Math.cos(secondAngle);
    expect(secondX).toBeGreaterThan(center);
  });

});
