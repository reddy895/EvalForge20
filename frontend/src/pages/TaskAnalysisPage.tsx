import React, { useEffect, useState } from 'react';
import {
  Layers,
  CheckCircle2,
  AlertTriangle,
  DollarSign,
  ChevronDown,
  ChevronRight,
  Info,
} from 'lucide-react';
import { api } from '../api/client';
import type { RunSummary, RunAnalysisResponse, TaskCategoryMetrics, BandMetrics } from '../api/types';
import { MetricCard } from '../components/dashboard/MetricCard';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import './TaskAnalysisPage.css';

export const TaskAnalysisPage: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [analysis, setAnalysis] = useState<RunAnalysisResponse | null>(null);
  const [isLoadingRuns, setIsLoadingRuns] = useState<boolean>(true);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  const loadRuns = async () => {
    setIsLoadingRuns(true);
    setError(null);
    try {
      const runList = await api.listEvaluations({ limit: 50 });
      setRuns(runList);
      if (runList.length > 0) {
        const firstCompleted = runList.find((r) => r.status === 'completed') || runList[0];
        setSelectedRunId(firstCompleted.run_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load evaluation runs');
    } finally {
      setIsLoadingRuns(false);
    }
  };

  const loadAnalysis = async (runId: string) => {
    if (!runId) return;
    setIsLoadingAnalysis(true);
    setError(null);
    try {
      const data = await api.getRunTaskAnalysis(runId);
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || `Failed to load task analysis for run '${runId}'`);
      setAnalysis(null);
    } finally {
      setIsLoadingAnalysis(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      loadAnalysis(selectedRunId);
    }
  }, [selectedRunId]);

  const complexityBandsList: BandMetrics[] = analysis?.complexity_bands
    ? Object.values(analysis.complexity_bands)
    : [];

  return (
    <div className="task-analysis-page">
      {/* Page Header */}
      <div className="task-analysis-header-row">
        <div>
          <h1 className="page-header-title">Task Capability & Complexity Analysis</h1>
          <p className="page-header-subtitle">
            Measured accuracy, error rates, and latencies stratified by task capability and complexity tier.
          </p>
        </div>

        <div className="task-analysis-controls">
          <label htmlFor="task-run-select" className="text-label" style={{ color: 'var(--text-secondary)' }}>
            Evaluation Run:
          </label>
          <select
            id="task-run-select"
            className="run-select-dropdown"
            value={selectedRunId}
            onChange={(e) => setSelectedRunId(e.target.value)}
            disabled={isLoadingRuns || runs.length === 0}
          >
            {runs.length === 0 ? (
              <option value="">No runs available</option>
            ) : (
              runs.map((r) => (
                <option key={r.run_id} value={r.run_id}>
                  {r.name} ({r.run_id.slice(0, 8)}) — {r.status}
                </option>
              ))
            )}
          </select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => loadAnalysis(selectedRunId)}
            loading={isLoadingAnalysis}
            disabled={!selectedRunId}
          >
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="toast-item error" role="alert">
          <AlertTriangle size={16} className="toast-icon" />
          <div className="toast-content">
            <div className="toast-title">Analysis Unavailable</div>
            <div className="toast-message">{error}</div>
          </div>
        </div>
      )}

      {/* Overview Metric Cards */}
      <div className="dashboard-metrics-grid">
        <MetricCard
          title="Target Model"
          value={analysis?.model_identifier || '—'}
          footer={`Provider: ${analysis?.provider_name || '—'}`}
          icon={<Layers size={14} />}
          isLoading={isLoadingAnalysis}
        />
        <MetricCard
          title="Overall Pass Rate"
          value={
            analysis?.pass_rate !== null && analysis?.pass_rate !== undefined
              ? `${(analysis.pass_rate * 100).toFixed(1)}%`
              : '—'
          }
          footer={`${analysis?.total_cases || 0} total evaluation cases`}
          icon={<CheckCircle2 size={14} />}
          isLoading={isLoadingAnalysis}
        />
        <MetricCard
          title="Task Categories"
          value={analysis?.task_categories?.length ?? 0}
          footer="Distinct functional capability domains"
          icon={<Layers size={14} />}
          isLoading={isLoadingAnalysis}
        />
        <MetricCard
          title="Cost Projection / 1k Tasks"
          value={
            analysis?.cost_breakdown?.cost_per_1k_tasks_usd !== null &&
            analysis?.cost_breakdown?.cost_per_1k_tasks_usd !== undefined
              ? `$${analysis.cost_breakdown.cost_per_1k_tasks_usd.toFixed(4)}`
              : '$0.00'
          }
          footer={
            analysis?.cost_breakdown?.is_cost_known
              ? analysis.cost_breakdown.assumptions || 'Based on measured token consumption'
              : 'Zero cloud API cost (Local inference)'
          }
          icon={<DollarSign size={14} />}
          isLoading={isLoadingAnalysis}
        />
      </div>

      {/* Complexity Tiers Breakdown */}
      <div className="dashboard-section">
        <div className="dashboard-section-title">Complexity Tiers Stratification</div>
        <p className="page-header-subtitle" style={{ marginBottom: 'var(--space-sm)' }}>
          Cases categorized into complexity bands based on input length, tool call depth, and reasoning requirements.
        </p>

        {complexityBandsList.length === 0 ? (
          <div className="empty-state-panel" style={{ background: 'var(--bg-secondary)', padding: 'var(--space-lg)' }}>
            <span style={{ color: 'var(--text-muted)' }}>
              No complexity tier classifications recorded for this run.
            </span>
          </div>
        ) : (
          <div className="complexity-tiers-grid">
            {complexityBandsList.map((band) => {
              const passPct =
                band.pass_rate !== null && band.pass_rate !== undefined
                  ? `${(band.pass_rate * 100).toFixed(1)}%`
                  : 'N/A';
              const latStr =
                band.mean_latency_ms !== null && band.mean_latency_ms !== undefined
                  ? `${band.mean_latency_ms.toFixed(1)} ms`
                  : '—';

              return (
                <div key={band.band} className="tier-card">
                  <div className="tier-card-header">
                    <span className="tier-card-title">{band.band} Complexity</span>
                    {!band.has_sufficient_data && (
                      <span
                        className="insufficient-data-badge"
                        title={band.insufficient_data_note || 'Fewer than 3 samples recorded in this tier'}
                      >
                        &lt; 3 samples
                      </span>
                    )}
                  </div>

                  <div className="tier-stat-row">
                    <span className="tier-stat-label">Total Test Cases:</span>
                    <span className="tier-stat-val">{band.total_cases}</span>
                  </div>
                  <div className="tier-stat-row">
                    <span className="tier-stat-label">Pass Rate:</span>
                    <span className="tier-stat-val">
                      <Badge
                        variant={
                          band.pass_rate === null
                            ? 'neutral'
                            : band.pass_rate >= 0.8
                            ? 'success'
                            : band.pass_rate >= 0.5
                            ? 'accent'
                            : 'error'
                        }
                      >
                        {passPct}
                      </Badge>
                    </span>
                  </div>
                  <div className="tier-stat-row">
                    <span className="tier-stat-label">Mean Latency:</span>
                    <span className="tier-stat-val">{latStr}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Task Capability Categories Table */}
      <div className="categories-table-container">
        <div className="categories-table-header">
          <div className="dashboard-section-title">Functional Task Capabilities</div>
          <span className="text-label" style={{ color: 'var(--text-muted)' }}>
            Click a category row to inspect representative failures
          </span>
        </div>

        {(!analysis?.task_categories || analysis.task_categories.length === 0) ? (
          <div style={{ padding: 'var(--space-md)', color: 'var(--text-muted)', fontSize: 'var(--font-size-sm)' }}>
            No category metadata available for this evaluation run.
          </div>
        ) : (
          <table className="subpanel-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-default)', textAlign: 'left', fontSize: '11px', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px' }}>Category</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Total Cases</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Passed</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Failed</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Pass Rate</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Mean Latency</th>
              </tr>
            </thead>
            <tbody>
              {analysis.task_categories.map((cat: TaskCategoryMetrics) => {
                const isExpanded = expandedCategory === cat.category;
                const passPct =
                  cat.pass_rate !== null && cat.pass_rate !== undefined
                    ? `${(cat.pass_rate * 100).toFixed(1)}%`
                    : '—';

                return (
                  <React.Fragment key={cat.category}>
                    <tr
                      className="category-row-clickable"
                      onClick={() => setExpandedCategory(isExpanded ? null : cat.category)}
                      style={{ borderBottom: '1px solid var(--border-subtle)', fontSize: 'var(--font-size-xs)' }}
                    >
                      <td style={{ padding: '10px 8px', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        <span style={{ textTransform: 'capitalize' }}>{cat.category}</span>
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontFamily: 'var(--font-family-mono)' }}>
                        {cat.total_cases}
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontFamily: 'var(--font-family-mono)', color: 'var(--status-success)' }}>
                        {cat.passed_cases}
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontFamily: 'var(--font-family-mono)', color: cat.failed_cases > 0 ? 'var(--status-error)' : 'var(--text-muted)' }}>
                        {cat.failed_cases}
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                        <Badge
                          variant={
                            cat.pass_rate === null
                              ? 'neutral'
                              : cat.pass_rate >= 0.8
                              ? 'success'
                              : cat.pass_rate >= 0.5
                              ? 'accent'
                              : 'error'
                          }
                        >
                          {passPct}
                        </Badge>
                      </td>
                      <td style={{ padding: '10px 8px', textAlign: 'right', fontFamily: 'var(--font-family-mono)' }}>
                        {cat.mean_latency_ms !== null ? `${cat.mean_latency_ms.toFixed(0)} ms` : '—'}
                      </td>
                    </tr>

                    {/* Expandable Failure Inspection Drawer */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={6} style={{ padding: '8px 12px', background: 'var(--bg-primary)' }}>
                          <div className="failures-card">
                            <span className="text-label" style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <Info size={12} /> Representative Failure Modes ({cat.failed_cases} total failures)
                            </span>
                            {(!cat.representative_failures || cat.representative_failures.length === 0) ? (
                              <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                                No failure cases recorded in this category.
                              </span>
                            ) : (
                              cat.representative_failures.map((f, idx) => (
                                <div key={idx} className="failure-item">
                                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                                    Case: {f.case_id}
                                  </div>
                                  <div style={{ color: 'var(--status-error)', marginBottom: '4px' }}>
                                    Reason: {f.error_message || 'Assertion failed'}
                                  </div>
                                  {f.input && (
                                    <div style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-family-mono)', fontSize: '10px' }}>
                                      Input: {f.input}
                                    </div>
                                  )}
                                </div>
                              ))
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
