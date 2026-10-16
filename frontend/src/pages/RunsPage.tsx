import React, { useEffect, useState, useMemo } from 'react';
import { Plus, RefreshCw, PlayCircle } from 'lucide-react';
import { api } from '../api/client';
import type { RunSummary } from '../api/types';
import { type NavRoute } from '../types/navigation';
import { Button } from '../components/ui/Button';
import { SearchBar } from '../components/ui/Input';
import { StatusPill } from '../components/ui/Badge';
import { DataTable, type Column } from '../components/ui/DataTable';
import './RunsPage.css';

interface RunsPageProps {
  onNavigate: (route: NavRoute, runId?: string) => void;
}

export const RunsPage: React.FC<RunsPageProps> = ({ onNavigate }) => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [minPassRateFilter, setMinPassRateFilter] = useState<string>('all');

  const fetchRuns = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listEvaluations({ limit: 100 });
      setRuns(data);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve evaluation runs from database');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const filteredRuns = useMemo(() => {
    return runs.filter((r) => {
      // Search matching run_id or name
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q || r.run_id.toLowerCase().includes(q) || r.name.toLowerCase().includes(q);

      // Status filter
      const matchesStatus =
        statusFilter === 'all' || r.status.toLowerCase() === statusFilter.toLowerCase();

      // Min pass rate
      let matchesPassRate = true;
      if (minPassRateFilter !== 'all') {
        const threshold = parseFloat(minPassRateFilter);
        matchesPassRate =
          r.pass_rate !== null && r.pass_rate !== undefined && Number(r.pass_rate) >= threshold;
      }

      return matchesSearch && matchesStatus && matchesPassRate;
    });
  }, [runs, searchQuery, statusFilter, minPassRateFilter]);

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
      header: 'Evaluation Run Name',
      sortable: true,
      render: (r) => (
        <div>
          <span style={{ fontWeight: 500 }}>{r.name}</span>
          {r.error_message && (
            <div
              style={{
                fontSize: '11px',
                color: 'var(--status-error)',
                marginTop: '2px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '400px',
              }}
            >
              {r.error_message}
            </div>
          )}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      width: '120px',
      render: (r) => <StatusPill status={r.status} />,
    },
    {
      key: 'pass_rate',
      header: 'Pass Rate',
      sortable: true,
      align: 'right',
      width: '100px',
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
      width: '110px',
      render: (r) => (
        <span className="font-mono tabular-nums">
          {r.completed_cases} / {r.total_cases}
          {r.failed_cases > 0 && (
            <span style={{ color: 'var(--status-error)', marginLeft: '4px' }}>
              ({r.failed_cases} failed)
            </span>
          )}
        </span>
      ),
    },
    {
      key: 'started_at',
      header: 'Created At',
      sortable: true,
      align: 'right',
      width: '160px',
      render: (r) => (
        <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          {r.started_at ? new Date(r.started_at).toLocaleString() : '—'}
        </span>
      ),
    },
  ];

  return (
    <div className="runs-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Evaluation Runs</h1>
          <p className="page-header-subtitle">
            Inspect execution history, analyze metric scoring breakdowns, and trace failures.
          </p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="outline"
            iconLeft={<RefreshCw size={13} />}
            loading={isLoading}
            onClick={fetchRuns}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            iconLeft={<Plus size={14} />}
            onClick={() => onNavigate('new-eval')}
            id="btn-runs-new-eval"
          >
            New Evaluation
          </Button>
        </div>
      </div>

      {error && (
        <div className="toast-item error" role="alert">
          <div className="toast-content">
            <div className="toast-title">Failed to Load Evaluation Runs</div>
            <div className="toast-message">{error}</div>
          </div>
        </div>
      )}

      {/* Filters Bar */}
      <div className="runs-filters-bar">
        <div className="runs-filters-left">
          <SearchBar
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
            placeholder="Search by run ID or name..."
          />
        </div>

        <div className="runs-filters-right">
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter runs by execution status"
          >
            <option value="all">All Execution Statuses</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
            <option value="queued">Queued</option>
          </select>

          <select
            className="filter-select"
            value={minPassRateFilter}
            onChange={(e) => setMinPassRateFilter(e.target.value)}
            aria-label="Filter runs by minimum pass rate"
          >
            <option value="all">Any Pass Rate</option>
            <option value="0.9">≥ 90% Pass Rate</option>
            <option value="0.75">≥ 75% Pass Rate</option>
            <option value="0.5">≥ 50% Pass Rate</option>
          </select>

          <span className="font-mono text-label" style={{ whiteSpace: 'nowrap' }}>
            {filteredRuns.length} of {runs.length} runs
          </span>
        </div>
      </div>

      {/* Runs Table */}
      <DataTable
        columns={columns}
        data={filteredRuns}
        keyExtractor={(r) => r.run_id}
        isLoading={isLoading}
        onRowClick={(r) => onNavigate('run-detail', r.run_id)}
        pageSize={20}
        emptyState={
          <div style={{ padding: 'var(--space-xl)', textAlign: 'center' }}>
            <PlayCircle size={28} style={{ color: 'var(--text-muted)', marginBottom: 'var(--space-sm)' }} />
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>No Evaluation Runs Found</div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
              {runs.length === 0
                ? 'No evaluations have been run yet. Launch your first evaluation.'
                : 'No evaluation runs match your active search filters.'}
            </div>
          </div>
        }
      />
    </div>
  );
};
