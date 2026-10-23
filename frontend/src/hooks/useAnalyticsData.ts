import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { AnalyticsOverview, CommitAnalytics } from '../types';

export function useAnalyticsData() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [commits, setCommits] = useState<CommitAnalytics | null>(null);
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [efficiency, setEfficiency] = useState<any[]>([]);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [ov, cm, lb, eff, tr] = await Promise.all([
        api.getAnalyticsOverview().catch(() => null),
        api.getCommitAnalytics().catch(() => null),
        api.getLeaderboard().catch(() => []),
        api.getEfficiencyMetrics().catch(() => []),
        api.getHistoricalTrends().catch(() => []),
      ]);
      setOverview(ov);
      setCommits(cm);
      setLeaderboard(Array.isArray(lb) ? lb : []);
      setEfficiency(Array.isArray(eff) ? eff : []);
      setTrends(Array.isArray(tr) ? tr : []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics telemetry');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return { overview, commits, leaderboard, efficiency, trends, loading, error, reload };
}
