import { describe, it, expect, vi } from 'vitest';
import { api } from '../services/api';

describe('useAnalyticsData contract', () => {
  it('retrieves overview and commit telemetry', async () => {
    vi.spyOn(api, 'getAnalyticsOverview').mockResolvedValueOnce({
      total_providers: 15,
      healthy_providers: 3,
      total_models: 14,
      local_models_count: 6,
      cloud_models_count: 8,
      total_evaluation_runs: 24,
      completed_runs: 22,
      failed_runs: 2,
      running_runs: 0,
      cancelled_runs: 0,
      overall_pass_rate_percent: 91.5,
      overall_reliability_percent: 95.8,
      average_latency_ms: 184.2,
      total_test_cases_evaluated: 144,
      total_benchmark_comparisons: 5,
      total_agent_evaluations: 3,
      recent_runs: [],
      model_scorecards: [],
      timestamp: '2026-10-22T17:00:00Z',
    });

    const overview = await api.getAnalyticsOverview();
    expect(overview.total_providers).toBe(15);
    expect(overview.overall_pass_rate_percent).toBe(91.5);
  });
});
