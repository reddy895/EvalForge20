import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../services/api';
import { CommitAnalytics, AnalyticsOverview } from '../types';

describe('Frontend API Service and Analytics Contract', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches verified repository commits matching 56 commit target requirements', async () => {
    const mockCommitPayload: CommitAnalytics = {
      target_commits: 56,
      total_verified_commits: 392,
      target_achieved: true,
      target_progress_percent: 700.0,
      status_label: 'Target Achieved (392 Verified Commits Exceeds 56 Target Requirement)',
      source: 'Local Git rev-list log data',
      time_range_start: '2026-10-15T00:00:00Z',
      time_range_end: '2026-10-21T23:59:59Z',
      author_distribution: {
        'reddy895 <praveenlk41@gmail.com>': 390,
        'PRAVEEN REDDY <praveenlk41@gmail.com>': 2,
      },
      daily_activity: [
        { date: '2026-10-15', count: 73, level: 3, sample_commits: [] },
        { date: '2026-10-16', count: 81, level: 4, sample_commits: [] },
        { date: '2026-10-17', count: 31, level: 2, sample_commits: [] },
        { date: '2026-10-18', count: 27, level: 1, sample_commits: [] },
        { date: '2026-10-19', count: 98, level: 4, sample_commits: [] },
        { date: '2026-10-20', count: 82, level: 4, sample_commits: [] },
      ],
      last_updated: '2026-10-22T17:00:00Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockCommitPayload,
    } as unknown as Response);

    const commitsData = await api.getCommitAnalytics();

    expect(commitsData.target_commits).toBe(56);
    expect(commitsData.target_achieved).toBe(true);
    expect(commitsData.total_verified_commits).toBe(392);
    expect(commitsData.total_verified_commits).toBeGreaterThanOrEqual(56);
    expect(commitsData.daily_activity.length).toBe(6);
    expect(commitsData.daily_activity[0].count).toBe(73);
  });

  it('fetches analytics overview metrics correctly', async () => {
    const mockOverview: AnalyticsOverview = {
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
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockOverview,
    } as unknown as Response);

    const overview = await api.getAnalyticsOverview();

    expect(overview.total_providers).toBe(15);
    expect(overview.total_models).toBe(14);
    expect(overview.completed_runs).toBe(22);
    expect(overview.overall_pass_rate_percent).toBe(91.5);
  });

  it('handles API errors gracefully with descriptive error message', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: async () => ({ error: { message: 'Provider gateway timeout' } }),
    } as unknown as Response);

    await expect(api.getAnalyticsOverview()).rejects.toThrow(
      'Provider gateway timeout'
    );
  });

  it('fetches empirical latency distributions with percentiles', async () => {
    const mockLatencyDist = [
      {
        model_id: 'qwen2.5:1.5b',
        model_name: 'Qwen 2.5 1.5B',
        sample_count: 8,
        mean_ms: 125.4,
        min_ms: 45.0,
        p10_ms: 50.0,
        p25_ms: 80.0,
        p50_ms: 120.0,
        p75_ms: 160.0,
        p90_ms: 210.0,
        p95_ms: 220.0,
        p99_ms: 225.0,
        max_ms: 230.0,
        raw_samples: [45.0, 80.0, 120.0, 230.0],
      },
    ];

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockLatencyDist,
    } as unknown as Response);

    const dist = await api.getLatencyDistribution();
    expect(dist.length).toBe(1);
    expect(dist[0].model_id).toBe('qwen2.5:1.5b');
    expect(dist[0].p50_ms).toBe(120.0);
    expect(dist[0].p95_ms).toBe(220.0);
    expect(dist[0].sample_count).toBe(8);
  });
});

