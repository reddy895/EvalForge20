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

  return (
    <div className="compare-metrics-card">
      <div className="compare-metrics-header">
        <span className="compare-metrics-title">Comparative Metric Benchmarks</span>
        <span className="font-mono text-label">
          {comparison.baseline_name} vs {comparison.candidate_name}
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
          {comparison.regressed_case_ids.length} regressions · {comparison.improved_case_ids.length} improvements
        </span>
      </div>

      <table className="data-table">
        <thead className="data-table-head">
          <tr>
            <th className="data-table-th">Benchmark Metric</th>
            <th className="data-table-th" style={{ textAlign: 'right' }}>
              Baseline: {comparison.baseline_name}
            </th>
            <th className="data-table-th" style={{ textAlign: 'right' }}>
              Candidate: {comparison.candidate_name}
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
              Overall Evaluation Score
            </td>
            <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
              —
            </td>
            <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
              —
            </td>
            <td className="data-table-td" style={{ textAlign: 'right' }}>
              <DeltaPill delta={comparison.score_delta} higherIsBetter={true} />
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
                delta={comparison.latency_delta_ms}
                higherIsBetter={false}
                format={(val) => `${val >= 0 ? '+' : ''}${val.toFixed(1)} ms`}
              />
            </td>
            <td className="data-table-td text-label" style={{ color: 'var(--text-muted)' }}>
              Lower is better
            </td>
          </tr>

          {/* Individual Evaluator Metric Deltas */}
          {metricKeys.map((metricId) => {
            const delta = metricDeltas[metricId];
            return (
              <tr key={metricId} className="data-table-tr">
                <td className="data-table-td font-mono">{metricId}</td>
                <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                  —
                </td>
                <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                  —
                </td>
                <td className="data-table-td" style={{ textAlign: 'right' }}>
                  <DeltaPill delta={delta} higherIsBetter={true} />
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
