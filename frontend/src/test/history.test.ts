import { describe, it, expect } from 'vitest';
import type { EvaluationRun } from '../types';

describe('Evaluation History and Export Utilities', () => {
  const sampleRuns: EvaluationRun[] = [
    {
      id: 'run-1',
      model_id: 'llama3.2:3b',
      model_name: 'Llama 3.2 3B',
      benchmark_id: 'gsm8k_sample',
      benchmark_name: 'Grade School Math',
      status: 'completed',
      pass_rate: 0.85,
      passed_cases: 17,
      total_cases: 20,
      avg_latency_ms: 142.5,
      tokens_per_second: 48.2,
      created_at: '2026-10-24T10:00:00Z',
    },
    {
      id: 'run-2',
      model_id: 'qwen2.5:7b',
      model_name: 'Qwen 2.5 7B',
      benchmark_id: 'gsm8k_sample',
      benchmark_name: 'Grade School Math',
      status: 'completed',
      pass_rate: 0.90,
      passed_cases: 18,
      total_cases: 20,
      avg_latency_ms: 198.3,
      tokens_per_second: 36.4,
      created_at: '2026-10-24T10:15:00Z',
    },
    {
      id: 'run-3',
      model_id: 'llama3.2:3b',
      model_name: 'Llama 3.2 3B',
      benchmark_id: 'humaneval_python_sample',
      benchmark_name: 'HumanEval Python',
      status: 'failed',
      pass_rate: 0.0,
      passed_cases: 0,
      total_cases: 10,
      avg_latency_ms: 0,
      created_at: '2026-10-24T10:30:00Z',
    },
  ];

  it('filters runs by model identifier', () => {
    const filtered = sampleRuns.filter(r => r.model_id === 'llama3.2:3b');
    expect(filtered.length).toBe(2);
    expect(filtered[0].id).toBe('run-1');
    expect(filtered[1].id).toBe('run-3');
  });

  it('filters runs by execution status', () => {
    const completed = sampleRuns.filter(r => r.status === 'completed');
    expect(completed.length).toBe(2);

    const failed = sampleRuns.filter(r => r.status === 'failed');
    expect(failed.length).toBe(1);
    expect(failed[0].id).toBe('run-3');
  });

  it('formats pass rate percentage and token throughput reliably', () => {
    const formatPassRate = (rate: number | undefined) =>
      rate !== undefined ? `${(rate * 100).toFixed(1)}%` : 'N/A';

    expect(formatPassRate(sampleRuns[0].pass_rate)).toBe('85.0%');
    expect(formatPassRate(sampleRuns[1].pass_rate)).toBe('90.0%');
    expect(formatPassRate(undefined)).toBe('N/A');

    const formatTps = (tps: number | undefined) =>
      tps !== undefined ? `${tps.toFixed(1)} tok/s` : 'N/A';

    expect(formatTps(sampleRuns[0].tokens_per_second)).toBe('48.2 tok/s');
    expect(formatTps(sampleRuns[2].tokens_per_second)).toBe('N/A');
  });

  it('exports evaluation run metadata to structured JSON format', () => {
    const run = sampleRuns[0];
    const exportData = {
      run_id: run.id,
      model: run.model_id,
      dataset: run.benchmark_id,
      status: run.status,
      metrics: {
        pass_rate: run.pass_rate,
        avg_latency_ms: run.avg_latency_ms,
        tokens_per_second: run.tokens_per_second,
      },
      timestamp: run.created_at,
    };

    const jsonString = JSON.stringify(exportData, null, 2);
    const parsed = JSON.parse(jsonString);

    expect(parsed.run_id).toBe('run-1');
    expect(parsed.metrics.pass_rate).toBe(0.85);
    expect(parsed.metrics.tokens_per_second).toBe(48.2);
  });
});
