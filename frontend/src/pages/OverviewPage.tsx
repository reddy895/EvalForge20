import React, { useEffect, useState, useMemo } from 'react';
import { Plus, Database, Activity, CheckCircle2, AlertOctagon, Clock } from 'lucide-react';
import { api } from '../api/client';
import type { RunSummary } from '../api/types';
import { type NavRoute } from '../types/navigation';
import { Button } from '../components/ui/Button';
import { StatusPill } from '../components/ui/Badge';
import { DataTable, type Column } from '../components/ui/DataTable';
import { MetricCard } from '../components/dashboard/MetricCard';
import { ScoreHistoryChart } from '../components/dashboard/ScoreHistoryChart';
import { ModelLeaderboard } from '../components/dashboard/ModelLeaderboard';
import { ActivityFeed } from '../components/dashboard/ActivityFeed';
import './OverviewPage.css';

interface OverviewPageProps {
  onNavigate: (route: NavRoute, runId?: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({ onNavigate }) => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    api
      .listEvaluations({ limit: 50 })
      .then((data) => {
        if (mounted) {
          setRuns(data);
          setError(null);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err.message || 'Failed to load evaluation overview metrics');
        }
      })
      .finally(() => {
        if (mounted) setIsLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Compute live summary statistics strictly from backend data
  const stats = useMemo(() => {
    const totalRuns = runs.length;
    const completedRuns = runs.filter((r) => r.status.toLowerCase() === 'completed');
    const failedRuns = runs.filter((r) => r.status.toLowerCase() === 'failed');

    const runsWithScore = completedRuns.filter((r) => r.pass_rate !== null && r.pass_rate !== undefined);
    const avgScore =
      runsWithScore.length > 0
        ? (runsWithScore.reduce((sum, r) => sum + Number(r.pass_rate), 0) / runsWithScore.length) * 100
        : null;

    const runsWithLatency = completedRuns.filter(
      (r) => (r as any).mean_latency_ms !== null && (r as any).mean_latency_ms !== undefined
    );
    const avgLatency =
      runsWithLatency.length > 0
        ? (runsWithLatency.reduce((sum, r) => sum + Number((r as any).mean_latency_ms), 0) /
            runsWithLatency.length).toFixed(1)
        : null;

    const failureRate = totalRuns > 0 ? (failedRuns.length / totalRuns) * 100 : 0;

    return {
      totalRuns,
      avgScore: avgScore !== null ? `${avgScore.toFixed(1)}%` : null,
      avgLatency,
      failureRate: `${failureRate.toFixed(1)}%`,
    };
  }, [runs]);

  const columns: Column<RunSummary>[] = [
    {
      key: 'run_id',
      header: 'Run ID',
      sortable: true,
      width: '140px',
      render: (r) => (
        <span className="font-mono" style={{ color: 'var(--accent-primary)', fontWeight: 500 }}>
          {r.run_id.substring(0, 14)}
        </span>
      ),
    },
    {
      key: 'name',
      header: 'Run Name / Target',
      sortable: true,
      render: (r) => <span style={{ fontWeight: 500 }}>{r.name}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      width: '110px',
      render: (r) => <StatusPill status={r.status} />,
    },
    {
      key: 'pass_rate',
      header: 'Score',
      sortable: true,
      align: 'right',
      width: '90px',
      render: (r) => (
        <span className="font-mono tabular-nums">
          {r.pass_rate !== null && r.pass_rate !== undefined
            ? `${(Number(r.pass_rate) * 100).toFixed(1)}%`
            : '—'}
        </span>
      ),
      sortValue: (r) => (r.pass_rate !== null && r.pass_rate !== undefined ? Number(r.pass_rate) : -1),
    },
    {
      key: 'cases',
      header: 'Cases',
      align: 'right',
      width: '90px',
      render: (r) => (
        <span className="font-mono tabular-nums">
          {r.completed_cases}/{r.total_cases}
        </span>
      ),
    },
    {
      key: 'started_at',
      header: 'Started At',
      sortable: true,
      align: 'right',
      width: '150px',
      render: (r) => (
        <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          {r.started_at ? new Date(r.started_at).toLocaleString() : '—'}
        </span>
      ),
    },
  ];

  return (
    <div className="overview-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Evaluation Overview</h1>
          <p className="page-header-subtitle">
            Measure quality. Compare models. Track regressions.
          </p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="secondary"
            iconLeft={<Database size={14} />}
            onClick={() => onNavigate('datasets')}
            id="btn-overview-import-dataset"
          >
            Import Dataset
          </Button>
          <Button
            variant="primary"
            iconLeft={<Plus size={14} />}
            onClick={() => onNavigate('new-eval')}
            id="btn-overview-new-eval"
          >
            New Evaluation
          </Button>
        </div>
      </div>

      {error && (
        <div className="toast-item error" style={{ marginBottom: 'var(--space-base)' }} role="alert">
          <AlertOctagon size={16} className="toast-icon" />
          <div className="toast-content">
            <div className="toast-title">Backend Telemetry Unreachable</div>
            <div className="toast-message">{error}</div>
          </div>
        </div>
      )}

      {/* Summary Metrics Cards */}
      <div className="dashboard-metrics-grid">
        <MetricCard
          title="Total Evaluation Runs"
          value={stats.totalRuns}
          footer="Persisted evaluation runs in database"
          icon={<Activity size={14} />}
          isLoading={isLoading}
        />
        <MetricCard
          title="Average Evaluation Score"
          value={stats.avgScore}
          footer="Mean pass rate across completed runs"
          icon={<CheckCircle2 size={14} />}
          isLoading={isLoading}
        />
        <MetricCard
          title="Average Latency"
          value={stats.avgLatency}
          unit={stats.avgLatency ? "ms" : undefined}
          footer="Mean per-case execution latency"
          icon={<Clock size={14} />}
          isLoading={isLoading}
        />
        <MetricCard
          title="Failure Rate"
          value={stats.failureRate}
          footer="Execution and provider error frequency"
          icon={<AlertOctagon size={14} />}
          isLoading={isLoading}
        />
      </div>

      {/* Visualizations Grid */}
      <div className="dashboard-visuals-grid">
        <ScoreHistoryChart runs={runs} isLoading={isLoading} />
        <ModelLeaderboard runs={runs} isLoading={isLoading} />
      </div>

      {/* Recent Runs Table */}
      <div className="dashboard-section">
        <div className="dashboard-section-title">Recent Runs</div>
        <DataTable
          columns={columns}
          data={runs.slice(0, 10)}
          keyExtractor={(r) => r.run_id}
          isLoading={isLoading}
          onRowClick={(r) => onNavigate('run-detail', r.run_id)}
          emptyMessage="No evaluation runs have been created yet. Launch an evaluation to measure model quality."
        />
      </div>

      {/* Platform Activity Feed */}
      <div className="dashboard-section">
        <ActivityFeed runs={runs} isLoading={isLoading} />
      </div>
    </div>
  );
};
