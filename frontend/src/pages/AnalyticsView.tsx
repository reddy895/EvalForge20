import React from 'react';
import { useAnalyticsData } from '../hooks/useAnalyticsData';
import { CommitActivityHeatmap } from '../charts/CommitActivityHeatmap';
import { ReliabilityAuditChart } from '../charts/ReliabilityAuditChart';

export const AnalyticsView: React.FC = () => {
  const { overview, commits, loading, error, reload } = useAnalyticsData();

  if (loading) {
    return <div className="p-8 text-center text-[#A7A29A]">Loading analytics telemetry...</div>;
  }

  if (error || !overview || !commits) {
    return (
      <div className="p-8 text-center space-y-3">
        <p className="text-sm text-red-400">Failed to load analytics: {error}</p>
        <button onClick={reload} className="px-4 py-1.5 rounded-xl bg-white/10 text-xs text-[#F5F0E7]">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5">
          <p className="text-xs text-[#A7A29A]">Total Providers</p>
          <p className="text-xl font-bold font-mono text-[#F5F0E7] mt-1">{overview.total_providers}</p>
        </div>
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5">
          <p className="text-xs text-[#A7A29A]">Total Models</p>
          <p className="text-xl font-bold font-mono text-[#F5F0E7] mt-1">{overview.total_models}</p>
        </div>
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5">
          <p className="text-xs text-[#A7A29A]">Overall Pass Rate</p>
          <p className="text-xl font-bold font-mono text-[#68B587] mt-1">{overview.overall_pass_rate_percent}%</p>
        </div>
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5">
          <p className="text-xs text-[#A7A29A]">Avg Latency</p>
          <p className="text-xl font-bold font-mono text-[#D9823B] mt-1">{overview.average_latency_ms}ms</p>
        </div>
      </div>

      <CommitActivityHeatmap data={commits} />

      <ReliabilityAuditChart
        completedRuns={overview.completed_runs}
        failedRuns={overview.failed_runs}
        timeoutRuns={0}
        reliabilityRate={overview.overall_reliability_percent}
      />
    </div>
  );
};
