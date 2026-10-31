import React from 'react';
import { useAnalyticsData } from '../hooks/useAnalyticsData';
import { CommitActivityHeatmap } from '../charts/CommitActivityHeatmap';
import { ReliabilityAuditChart } from '../charts/ReliabilityAuditChart';
import { AccuracyQualityChart } from '../charts/AccuracyQualityChart';
import { LatencyComparisonChart } from '../charts/LatencyComparisonChart';
import { EfficiencyMetricsChart } from '../charts/EfficiencyMetricsChart';
import { ModelEfficiencyChart } from '../charts/ModelEfficiencyChart';
import { HistoricalTrendsChart } from '../charts/HistoricalTrendsChart';

export const AnalyticsView: React.FC = () => {
  const { overview, commits, leaderboard, efficiency, trends, loading, error, reload } = useAnalyticsData();

  if (loading) {
    return <div className="p-8 text-center text-[#A7A29A] font-mono">Loading analytics telemetry...</div>;
  }

  if (error || !overview) {
    return (
      <div className="p-8 text-center space-y-3">
        <p className="text-sm text-red-400">Failed to load analytics: {error || 'No overview data'}</p>
        <button onClick={reload} className="px-4 py-1.5 rounded-xl bg-white/10 text-xs text-[#F5F0E7] cursor-pointer">Retry</button>
      </div>
    );
  }

  const qualityData = leaderboard.map((l: any) => ({
    modelName: l.model_name || l.model_id,
    accuracy: Number(((l.pass_rate || 0) * 100).toFixed(1)),
    passedCount: l.passed_cases || 0,
    totalCount: l.total_cases || 0,
  }));

  const latencyData = leaderboard
    .filter(
      (l: any) =>
        (l.median_latency_ms !== null && l.median_latency_ms !== undefined && l.median_latency_ms > 0) ||
        (l.avg_latency_ms !== null && l.avg_latency_ms !== undefined && l.avg_latency_ms > 0)
    )
    .map((l: any) => {
      const med = l.median_latency_ms !== null && l.median_latency_ms !== undefined ? l.median_latency_ms : l.avg_latency_ms;
      const p95 = l.p95_latency_ms !== null && l.p95_latency_ms !== undefined ? l.p95_latency_ms : med;
      return {
        modelName: l.model_name || l.model_id,
        medianMs: Number(med.toFixed(1)),
        p95Ms: Number(p95.toFixed(1)),
      };
    });

  const efficiencyData = efficiency.map((e: any) => ({
    modelName: e.model_name || e.model_id,
    tokensPerSecond: e.tokens_per_second ? Number(e.tokens_per_second.toFixed(1)) : null,
    avgLatencyMs: e.avg_latency_ms ?? null,
    avgDurationSec: Number(((e.total_duration_ms || 1000) / 1000).toFixed(2)),
    efficiencyScore:
      e.efficiency_score !== undefined && e.efficiency_score !== null
        ? Number(e.efficiency_score.toFixed(1))
        : e.tokens_per_second && e.avg_latency_ms
        ? Number((e.tokens_per_second / (e.avg_latency_ms / 1000)).toFixed(1))
        : null,
  }));

  const trendPoints = trends.map((t: any) => ({
    date: t.date || (t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : 'Recent'),
    passRate: Number(((t.pass_rate || 0) * 100).toFixed(1)),
    latencyMs: Number((t.avg_latency_ms || 0).toFixed(1)),
  }));

  return (
    <div className="space-y-6">
      {/* Top Telemetry KPI Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5 shadow-sm">
          <p className="text-xs text-[#A7A29A]">Total Providers</p>
          <p className="text-xl font-bold font-mono text-[#F5F0E7] mt-1">{overview.total_providers}</p>
        </div>
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5 shadow-sm">
          <p className="text-xs text-[#A7A29A]">Catalog Models</p>
          <p className="text-xl font-bold font-mono text-[#F5F0E7] mt-1">{overview.total_models}</p>
        </div>
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5 shadow-sm">
          <p className="text-xs text-[#A7A29A]">Overall Pass Rate</p>
          <p className="text-xl font-bold font-mono text-[#14B8A6] mt-1">{overview.overall_pass_rate_percent}%</p>
        </div>
        <div className="p-4 bg-[#1F201D] rounded-2xl border border-white/5 shadow-sm">
          <p className="text-xs text-[#A7A29A]">Mean Response Latency</p>
          <p className="text-xl font-bold font-mono text-[#0D9488] mt-1">{overview.average_latency_ms} ms</p>
        </div>
      </div>

      {/* Grid of Empirical Accuracy & Latency 2D Bar Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AccuracyQualityChart data={qualityData} />
        <LatencyComparisonChart records={latencyData} />
      </div>

      {/* Grid of Throughput & Efficiency 2D Bar Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EfficiencyMetricsChart rows={efficiencyData} />
        <ModelEfficiencyChart rows={efficiencyData} />
      </div>

      {/* Reliability Execution Breakdown & Historical Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ReliabilityAuditChart
          completedRuns={overview.completed_runs}
          failedRuns={overview.failed_runs}
          timeoutRuns={0}
          reliabilityRate={overview.overall_reliability_percent}
        />
        <HistoricalTrendsChart points={trendPoints} />
      </div>

      {/* Git Commit Verification Heatmap */}
      {commits && <CommitActivityHeatmap data={commits} />}
    </div>
  );
};

