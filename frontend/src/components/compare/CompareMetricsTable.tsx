import React from 'react';
import { CheckCircle2, AlertOctagon } from 'lucide-react';
import type { ComparisonResult } from '../../api/types';
import { DeltaPill } from '../ui/Badge';
import './CompareMetricsTable.css';

interface CompareMetricsTableProps {
  comparison: ComparisonResult;
}

export const CompareMetricsTable: React.FC<CompareMetricsTableProps> = ({ comparison }) => {
  const metricDeltas = comparison.metric_deltas || {};
  const metricKeys = Object.keys(metricDeltas);

  const baseLabel = comparison.baseline_model || comparison.baseline_name || comparison.baseline_run_id.slice(0, 8);
  const candLabel = comparison.candidate_model || comparison.candidate_name || comparison.candidate_run_id.slice(0, 8);

  const scoreDelta = comparison.pass_rate_delta ?? comparison.score_delta ?? 0;
  const latDelta = comparison.mean_latency_delta_ms ?? comparison.latency_delta_ms ?? 0;
  const regressedCount = comparison.regressed_cases?.length ?? comparison.regressed_case_ids?.length ?? 0;
  const improvedCount = comparison.improved_cases?.length ?? comparison.improved_case_ids?.length ?? 0;

  return (
    <div className="compare-metrics-card">
      <div className="compare-metrics-header">
        <span className="compare-metrics-title">Comparative Metric Benchmarks</span>
        <span className="font-mono text-label">
          {baseLabel} vs {candLabel}
        </span>
      </div>

      {/* Regression Threshold Status Banner */}
      <div
        className={`compare-regression-status-box ${
          comparison.passed_regression_gate ? 'passed' : 'failed'
        }`}
      >
        <div className="flex-row gap-xs" style={{ fontWeight: 600, fontSize: 'var(--font-size-xs)' }}>
          {comparison.passed_regression_gate ? (
            <>
              <CheckCircle2 size={16} />
              <span>Regression Gate Passed: No unacceptable metric degradation.</span>
            </>
          ) : (
            <>
              <AlertOctagon size={16} />
              <span>Regression Gate Failed: Performance dropped beyond acceptable thresholds.</span>
            </>
          )}
        </div>
        <span className="font-mono" style={{ fontSize: '11px' }}>
          {regressedCount} regressions · {improvedCount} improvements
        </span>
      </div>

      <table className="data-table">
        <thead className="data-table-head">
          <tr>
            <th className="data-table-th">Benchmark Metric</th>
            <th className="data-table-th" style={{ textAlign: 'right' }}>
              Baseline: {baseLabel}
            </th>
            <th className="data-table-th" style={{ textAlign: 'right' }}>
              Candidate: {candLabel}
            </th>
            <th className="data-table-th" style={{ textAlign: 'right' }}>
              Delta / Change
            </th>
            <th className="data-table-th">Semantics</th>
          </tr>
        </thead>
        <tbody>
          {/* Overall Pass Rate Row */}
          <tr className="data-table-tr">
            <td className="data-table-td" style={{ fontWeight: 600 }}>
              Overall Pass Rate
            </td>
            <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
              —
            </td>
            <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
              —
            </td>
            <td className="data-table-td" style={{ textAlign: 'right' }}>
              <DeltaPill delta={scoreDelta} higherIsBetter={true} />
            </td>
            <td className="data-table-td text-label" style={{ color: 'var(--text-muted)' }}>
              Higher is better
            </td>
          </tr>

          {/* Latency Delta Row */}
          <tr className="data-table-tr">
            <td className="data-table-td" style={{ fontWeight: 600 }}>
              Mean Per-Case Latency
            </td>
            <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
              —
            </td>
            <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
              —
            </td>
            <td className="data-table-td" style={{ textAlign: 'right' }}>
              <DeltaPill
                delta={latDelta}
                higherIsBetter={false}
                format={(val) => `${val >= 0 ? '+' : ''}${val.toFixed(1)} ms`}
              />
            </td>
            <td className="data-table-td text-label" style={{ color: 'var(--text-muted)' }}>
              Lower is better
            </td>
          </tr>

          {/* Cost Delta Row */}
          {comparison.cost_delta_usd != null && (
            <tr className="data-table-tr">
              <td className="data-table-td" style={{ fontWeight: 600 }}>
                Estimated Total Cost Delta
              </td>
              <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                —
              </td>
              <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                —
              </td>
              <td className="data-table-td" style={{ textAlign: 'right' }}>
                <DeltaPill
                  delta={comparison.cost_delta_usd}
                  higherIsBetter={false}
                  format={(val) => `${val >= 0 ? '+' : ''}$${val.toFixed(4)}`}
                />
              </td>
              <td className="data-table-td text-label" style={{ color: 'var(--text-muted)' }}>
                Lower is better
              </td>
            </tr>
          )}

          {/* Individual Evaluator Metric Deltas */}
          {metricKeys.map((metricId) => {
            const raw = metricDeltas[metricId];
            const isObj = typeof raw === 'object' && raw !== null;
            const deltaVal = isObj ? raw.delta : raw;
            const baseVal = isObj && raw.baseline_value != null ? Number(raw.baseline_value).toFixed(3) : '—';
            const candVal = isObj && raw.candidate_value != null ? Number(raw.candidate_value).toFixed(3) : '—';

            return (
              <tr key={metricId} className="data-table-tr">
                <td className="data-table-td font-mono">{metricId}</td>
                <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                  {baseVal}
                </td>
                <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                  {candVal}
                </td>
                <td className="data-table-td" style={{ textAlign: 'right' }}>
                  <DeltaPill delta={deltaVal ?? 0} higherIsBetter={true} />
                </td>
                <td className="data-table-td text-label" style={{ color: 'var(--text-muted)' }}>
                  Higher is better
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
