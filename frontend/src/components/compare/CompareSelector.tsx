import React from 'react';
import { GitCompare, AlertTriangle } from 'lucide-react';
import type { RunSummary } from '../../api/types';
import './CompareSelector.css';

interface CompareSelectorProps {
  runs: RunSummary[];
  baselineId: string;
  candidateId: string;
  onBaselineChange: (id: string) => void;
  onCandidateChange: (id: string) => void;
  allowDifferentDatasets: boolean;
  onToggleAllowDifferentDatasets: (allow: boolean) => void;
  isCompatible: boolean;
}

export const CompareSelector: React.FC<CompareSelectorProps> = ({
  runs,
  baselineId,
  candidateId,
  onBaselineChange,
  onCandidateChange,
  allowDifferentDatasets,
  onToggleAllowDifferentDatasets,
  isCompatible,
}) => {
  return (
    <div className="compare-selector-card">
      <div className="flex-between">
        <div className="flex-row gap-xs">
          <GitCompare size={15} color="var(--accent-primary)" />
          <span className="text-label">Select Evaluation Benchmarks</span>
        </div>
        <span className="font-mono text-label">
          {runs.length} runs eligible for regression comparison
        </span>
      </div>

      <div className="compare-selector-grid">
        {/* Baseline Selection */}
        <div className="compare-run-box baseline">
          <span className="text-label">Baseline Benchmark</span>
          <select
            className="input-control font-mono"
            value={baselineId}
            onChange={(e) => onBaselineChange(e.target.value)}
            id="select-baseline-run"
            aria-label="Select baseline evaluation run"
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.name} ({r.run_id.substring(0, 10)}) — Score:{' '}
                {r.pass_rate !== null ? `${(Number(r.pass_rate) * 100).toFixed(0)}%` : '—'}
              </option>
            ))}
          </select>
        </div>

        <div className="compare-vs-icon">VS</div>

        {/* Candidate Selection */}
        <div className="compare-run-box candidate">
          <span className="text-label" style={{ color: 'var(--accent-primary)' }}>
            Candidate Benchmark
          </span>
          <select
            className="input-control font-mono"
            value={candidateId}
            onChange={(e) => onCandidateChange(e.target.value)}
            id="select-candidate-run"
            aria-label="Select candidate evaluation run"
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.name} ({r.run_id.substring(0, 10)}) — Score:{' '}
                {r.pass_rate !== null ? `${(Number(r.pass_rate) * 100).toFixed(0)}%` : '—'}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!isCompatible && (
        <div className="compatibility-warning-box">
          <AlertTriangle size={15} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ flex: 1 }}>
            <strong>Dataset Discrepancy Detected:</strong> The selected runs were evaluated on different datasets or dataset versions. Comparing metrics across disparate test suites can be misleading.
            <div style={{ marginTop: '6px' }}>
              <label style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={allowDifferentDatasets}
                  onChange={(e) => onToggleAllowDifferentDatasets(e.target.checked)}
                />
                <span>Allow comparison across different datasets anyway</span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
