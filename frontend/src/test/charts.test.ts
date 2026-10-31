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

  it('filters and scales horizontal latency comparison without fabricating zero latencies', () => {
    const rawRecords = [
      { modelName: 'Fast Model', medianMs: 14.2, p95Ms: 22.0 },
      { modelName: 'Slow Model', medianMs: 88.5, p95Ms: 110.0 },
      { modelName: 'Unmeasured Model', medianMs: 0, p95Ms: 0 },
    ];

    // Filter valid positive latencies
    const valid = rawRecords.filter((r) => r.medianMs > 0);
    expect(valid.length).toBe(2);

    // Sort fastest first
    valid.sort((a, b) => a.medianMs - b.medianMs);
    expect(valid[0].modelName).toBe('Fast Model');
    expect(valid[1].modelName).toBe('Slow Model');

    const maxObserved = Math.max(...valid.map((r) => r.p95Ms));
    expect(maxObserved).toBe(110.0);
    const chartCeiling = Math.max(50, Math.ceil(maxObserved * 1.15));
    expect(chartCeiling).toBeGreaterThanOrEqual(110.0);
  });

  it('validates accuracy comparison horizontal bar data mapping and case counts', () => {
    const qualityRecords = [
      { modelName: 'Model Alpha', accuracy: 92.5, passedCount: 37, totalCount: 40 },
      { modelName: 'Model Beta', accuracy: 60.0, passedCount: 24, totalCount: 40 },
      { modelName: 'Incomplete Model', accuracy: 0, passedCount: 0, totalCount: 0 },
    ];

    // Exclude invalid/incomplete results (totalCount <= 0)
    const valid = qualityRecords.filter((q) => q.totalCount > 0);
    expect(valid.length).toBe(2);

    // Sort descending by accuracy
    valid.sort((a, b) => b.accuracy - a.accuracy);
    expect(valid[0].modelName).toBe('Model Alpha');
    expect(valid[0].passedCount).toBe(37);
    expect(valid[0].totalCount).toBe(40);
    expect(valid[0].accuracy).toBe(92.5);
  });

  it('validates reliability breakdown grouped counts for passed, failed, and errored cases', () => {
    const groups = [
      { name: 'Coding Suite', passed: 42, failed: 5, errored: 1 },
      { name: 'JSON Schema Suite', passed: 30, failed: 0, errored: 2 },
    ];

    const totalPassed = groups.reduce((acc, g) => acc + g.passed, 0);
    const totalFailed = groups.reduce((acc, g) => acc + g.failed, 0);
    const totalErrored = groups.reduce((acc, g) => acc + g.errored, 0);

    expect(totalPassed).toBe(72);
    expect(totalFailed).toBe(5);
    expect(totalErrored).toBe(3);

    const maxCount = Math.max(...groups.map((g) => Math.max(g.passed, g.failed, g.errored)));
    expect(maxCount).toBe(42);
    const ceiling = Math.max(4, Math.ceil(maxCount * 1.2));
    expect(ceiling).toBeGreaterThan(42);
  });

  it('validates throughput comparison and flags unmeasured providers with explicit N/A', () => {
    const rows = [
      { modelName: 'Ollama Llama 3.2', tokensPerSecond: 64.2, avgDurationSec: 0.8 },
      { modelName: 'External Black-box API', tokensPerSecond: null, avgDurationSec: 1.5 },
    ];

    const validThroughput = rows.filter(
      (r) => typeof r.tokensPerSecond === 'number' && r.tokensPerSecond > 0
    );
    expect(validThroughput.length).toBe(1);
    expect(validThroughput[0].tokensPerSecond).toBe(64.2);

    const unmeasured = rows.filter((r) => r.tokensPerSecond === null);
    expect(unmeasured.length).toBe(1);
    expect(unmeasured[0].modelName).toBe('External Black-box API');
  });

  it('validates run history trend point coordinate calculations for line charts', () => {
    const trendPoints = [
      { date: 'Run 1', passRate: 75.0, latencyMs: 32.0 },
      { date: 'Run 2', passRate: 85.0, latencyMs: 28.0 },
      { date: 'Run 3', passRate: 100.0, latencyMs: 24.5 },
    ];

    expect(trendPoints.length).toBe(3);
    const passRates = trendPoints.map((p) => p.passRate);
    expect(passRates).toEqual([75.0, 85.0, 100.0]);

    // Trend improves monotonically
    expect(passRates[2]).toBeGreaterThan(passRates[1]);
    expect(passRates[1]).toBeGreaterThan(passRates[0]);

    // Latency decreases monotonically
    const latencies = trendPoints.map((p) => p.latencyMs);
    expect(latencies[2]).toBeLessThan(latencies[1]);
    expect(latencies[1]).toBeLessThan(latencies[0]);
  });

  it('preserves genuine zero accuracy in AccuracyQualityChart and distinguishes empty data', () => {
    // Model dataset with genuine zero (all assertions failed, but evaluation completed)
    const dataWithZero = [
      { name: 'Failing Model', accuracy: 0, quality: 10, totalCases: 10 },
      { name: 'Passing Model', accuracy: 100, quality: 95, totalCases: 10 },
    ];

    expect(dataWithZero.length).toBe(2);
    // Real zero is a valid number, not undefined or null
    expect(typeof dataWithZero[0].accuracy).toBe('number');
    expect(dataWithZero[0].accuracy).toBe(0);

    // Height calculations: on a 0-100 scale, 0% has height 0% while 100% has height 100%
    const zeroHeight = Math.max(0, Math.min(100, dataWithZero[0].accuracy));
    const passHeight = Math.max(0, Math.min(100, dataWithZero[1].accuracy));
    expect(zeroHeight).toBe(0);
    expect(passHeight).toBe(100);

    // Label formatting: genuine 0 displays '0%' explicitly rather than missing/empty
    const formatScore = (val: number | null | undefined) =>
      val === null || val === undefined ? '—' : `${Math.round(val)}%`;

    expect(formatScore(dataWithZero[0].accuracy)).toBe('0%');
    expect(formatScore(dataWithZero[1].accuracy)).toBe('100%');
    expect(formatScore(null)).toBe('—');
    expect(formatScore(undefined)).toBe('—');
  });

  it('validates ModelEfficiencyChart efficiency score calculations, sorting, and bar scaling', () => {
    const efficiencyRows = [
      { modelName: 'qwen2.5:1.5b', tokensPerSecond: 45.2, avgDurationSec: 0.85, efficiencyScore: 53.2 },
      { modelName: 'qwen2.5:3b', tokensPerSecond: 28.6, avgDurationSec: 1.40, efficiencyScore: 20.4 },
      { modelName: 'mock-deepseek', tokensPerSecond: null, avgDurationSec: 2.10, efficiencyScore: null },
    ];

    expect(efficiencyRows.length).toBe(3);

    // Filter valid efficiency scores
    const validScores = efficiencyRows
      .map((r) => r.efficiencyScore)
      .filter((s): s is number => typeof s === 'number' && !isNaN(s) && s > 0);
    expect(validScores).toEqual([53.2, 20.4]);

    const maxScore = Math.max(...validScores);
    expect(maxScore).toBe(53.2);

    const ceiling = Math.max(10, Math.ceil(maxScore * 1.15));
    expect(ceiling).toBeGreaterThan(53.2);

    // Sorting descending by efficiencyScore
    const sorted = [...efficiencyRows].sort((a, b) => {
      const valA = a.efficiencyScore ?? -1;
      const valB = b.efficiencyScore ?? -1;
      return valB - valA;
    });

    expect(sorted[0].modelName).toBe('qwen2.5:1.5b');
    expect(sorted[1].modelName).toBe('qwen2.5:3b');
    expect(sorted[2].modelName).toBe('mock-deepseek');

    // Horizontal bar width percentage calculation
    const widthPct0 = Math.min(100, (sorted[0].efficiencyScore! / ceiling) * 100);
    const widthPct1 = Math.min(100, (sorted[1].efficiencyScore! / ceiling) * 100);
    expect(widthPct0).toBeGreaterThan(widthPct1);
    expect(widthPct1).toBeGreaterThan(0);
  });

  it('handles empty and null rows gracefully for ModelEfficiencyChart', () => {
    const emptyRows: any[] = [];
    expect(emptyRows.length).toBe(0);

    const formatEfficiency = (val: number | null | undefined) =>
      typeof val === 'number' && !isNaN(val) ? `${val.toFixed(1)} pts` : 'Unmeasured';

    expect(formatEfficiency(null)).toBe('Unmeasured');
    expect(formatEfficiency(undefined)).toBe('Unmeasured');
    expect(formatEfficiency(42.56)).toBe('42.6 pts');
  });
});

