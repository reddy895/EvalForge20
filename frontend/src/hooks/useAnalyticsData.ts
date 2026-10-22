import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { AnalyticsOverview, CommitAnalytics } from '../types';

export function useAnalyticsData() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [commits, setCommits] = useState<CommitAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [ov, cm] = await Promise.all([
        api.getAnalyticsOverview(),
        api.getCommitAnalytics(),
      ]);
      setOverview(ov);
      setCommits(cm);
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

  return { overview, commits, loading, error, reload };
}
