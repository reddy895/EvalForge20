import React from 'react';
import type { ComparisonResult } from '../../api/types';
import { Badge } from '../ui/Badge';
import './RegressionInspector.css';

interface RegressionInspectorProps {
  comparison: ComparisonResult;
}

export const RegressionInspector: React.FC<RegressionInspectorProps> = ({ comparison }) => {
  const disagreements = comparison.disagreements || [];
  const regressions: string[] = comparison.regressed_case_ids || (comparison.regressed_cases || []).map((c) => c.case_id);
  const improvements: string[] = comparison.improved_case_ids || (comparison.improved_cases || []).map((c) => c.case_id);

  const baseLabel = comparison.baseline_model || comparison.baseline_name || 'Baseline';
  const candLabel = comparison.candidate_model || comparison.candidate_name || 'Candidate';

  return (
    <div className="regression-inspector-card">
      <div className="regression-inspector-header">
        <span className="case-results-title">Per-Case Regressions & Output Differences</span>
        <div className="flex-row gap-xs">
          <Badge variant="error">{regressions.length} Regressions</Badge>
          <Badge variant="success">{improvements.length} Improvements</Badge>
        </div>
      </div>

      {disagreements.length === 0 ? (
        <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
          No case-level score disagreements between baseline and candidate benchmarks.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {disagreements.map((d) => {
            const isRegression = regressions.includes(d.case_id);
            const isImprovement = improvements.includes(d.case_id);

            return (
              <div key={d.case_id} className="diff-case-item">
                <div className="diff-case-header">
                  <div className="flex-row gap-xs">
                    <span className="font-mono" style={{ fontWeight: 600 }}>
                      Case: {d.case_id}
                    </span>
                    {isRegression && <Badge variant="error">Regression</Badge>}
                    {isImprovement && <Badge variant="success">Improvement</Badge>}
                  </div>
                  <div className="flex-row gap-xs">
                    <span className="font-mono text-label">
                      Baseline: {d.baseline_passed ? 'PASS' : 'FAIL'}
                    </span>
                    <span className="font-mono text-label">→</span>
                    <span className="font-mono text-label">
                      Candidate: {d.candidate_passed ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                </div>

                {/* Side-by-Side Outputs */}
                <div className="diff-outputs-grid">
                  <div className={`diff-output-box ${d.baseline_passed ? 'baseline-pass' : ''}`}>
                    <span className="diff-output-title">
                      Baseline Output ({baseLabel}):
                    </span>
                    <div className="diff-output-text">
                      {d.baseline_output || <span style={{ color: 'var(--text-muted)' }}>—</span>}
                    </div>
                  </div>

                  <div className={`diff-output-box ${!d.candidate_passed ? 'candidate-fail' : ''}`}>
                    <span className="diff-output-title">
                      Candidate Output ({candLabel}):
                    </span>
                    <div className="diff-output-text">
                      {d.candidate_output || <span style={{ color: 'var(--text-muted)' }}>—</span>}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
