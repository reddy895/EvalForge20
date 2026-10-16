import React from 'react';
import { CheckCircle2, Clock, Zap, AlertTriangle } from 'lucide-react';
import type { AggregateMetrics } from '../../api/types';
import { MetricCard } from '../dashboard/MetricCard';
import './RunMetricsBreakdown.css';

interface RunMetricsBreakdownProps {
  aggregates: AggregateMetrics | null;
}

export const RunMetricsBreakdown: React.FC<RunMetricsBreakdownProps> = ({ aggregates }) => {
  if (!aggregates) {
    return (
      <div className="subpanel-card">
        <span className="subpanel-title">Aggregate Scoring</span>
        <div style={{ color: 'var(--text-muted)', fontSize: 'var(--font-size-xs)' }}>
          Aggregate metrics not yet compiled for this evaluation run.
        </div>
      </div>
    );
  }

  const passRateStr =
    aggregates.pass_rate !== null && aggregates.pass_rate !== undefined
      ? `${(aggregates.pass_rate * 100).toFixed(1)}%`
      : '—';

  const meanLatencyStr =
    aggregates.mean_latency_ms !== null && aggregates.mean_latency_ms !== undefined
      ? `${aggregates.mean_latency_ms.toFixed(1)} ms`
      : '—';

  const p95LatencyStr =
    aggregates.p95_latency_ms !== null && aggregates.p95_latency_ms !== undefined
      ? `${aggregates.p95_latency_ms.toFixed(1)} ms`
      : '—';

  const totalTokensStr =
    aggregates.total_tokens !== null && aggregates.total_tokens !== undefined
      ? aggregates.total_tokens.toLocaleString()
      : 'N/A';

  const metricKeys = Object.keys(aggregates.metric_averages || {});
  const categoryKeys = Object.keys(aggregates.category_performance || {});
  const errorKeys = Object.keys(aggregates.error_distribution || {});

  return (
    <div className="run-metrics-container">
      {/* 4 Summary Cards */}
      <div className="metrics-summary-row">
        <MetricCard
          title="Overall Pass Rate"
          value={passRateStr}
          footer={`${aggregates.completed_cases - aggregates.failed_cases} of ${aggregates.total_cases} cases passed`}
          icon={<CheckCircle2 size={14} />}
        />
        <MetricCard
          title="Mean Latency"
          value={meanLatencyStr}
          footer="Average response time per test case"
          icon={<Clock size={14} />}
        />
        <MetricCard
          title="P95 Latency"
          value={p95LatencyStr}
          footer="95th percentile execution latency"
          icon={<Clock size={14} />}
        />
        <MetricCard
          title="Total Tokens"
          value={totalTokensStr}
          footer="Prompt and completion token sum"
          icon={<Zap size={14} />}
        />
      </div>

      {/* Subpanels Grid */}
      <div className="metrics-subpanels-grid">
        {/* Metric Averages Subpanel */}
        <div className="subpanel-card">
          <span className="subpanel-title">Metric Performance</span>
          {metricKeys.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
              No individual metric breakdowns recorded.
            </div>
          ) : (
            <table className="subpanel-table">
              <tbody>
                {metricKeys.map((k) => {
                  const avg = aggregates.metric_averages[k];
                  const pr = aggregates.metric_pass_rates?.[k];

                  return (
                    <tr key={k} className="subpanel-tr">
                      <td className="subpanel-td-name">{k}</td>
                      <td className="subpanel-td-val">
                        Score: {(avg * 100).toFixed(1)}%
                        {pr !== undefined && (
                          <span style={{ color: 'var(--text-secondary)', marginLeft: '8px' }}>
                            (Pass: {(pr * 100).toFixed(1)}%)
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Category Performance Subpanel */}
        <div className="subpanel-card">
          <span className="subpanel-title">Category Breakdown</span>
          {categoryKeys.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
              Test cases did not specify categorical tagging.
            </div>
          ) : (
            <table className="subpanel-table">
              <tbody>
                {categoryKeys.map((cat) => {
                  const perf = aggregates.category_performance[cat] || {};
                  const catPass = perf.pass_rate !== undefined ? `${(perf.pass_rate * 100).toFixed(1)}%` : '—';
                  const catCases = perf.total_cases ?? '—';

                  return (
                    <tr key={cat} className="subpanel-tr">
                      <td className="subpanel-td-name">{cat}</td>
                      <td className="subpanel-td-val">
                        <span>{catPass}</span>
                        <span style={{ color: 'var(--text-secondary)', marginLeft: '8px', fontSize: '11px' }}>
                          ({catCases} cases)
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Error Distribution Subpanel (if any errors exist) */}
      {errorKeys.length > 0 && (
        <div className="subpanel-card" style={{ borderColor: 'var(--status-error-border)' }}>
          <div className="flex-row gap-xs" style={{ color: 'var(--status-error)' }}>
            <AlertTriangle size={14} />
            <span className="subpanel-title" style={{ color: 'var(--status-error)' }}>
              Execution & Provider Errors
            </span>
          </div>
          <table className="subpanel-table">
            <tbody>
              {errorKeys.map((errCat) => (
                <tr key={errCat} className="subpanel-tr">
                  <td className="subpanel-td-name" style={{ color: 'var(--status-error)' }}>
                    {errCat}
                  </td>
                  <td className="subpanel-td-val" style={{ color: 'var(--status-error)' }}>
                    {aggregates.error_distribution[errCat]} occurrences
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
