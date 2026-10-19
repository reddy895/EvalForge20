import React, { useState, useEffect } from 'react';
import type { EvaluationRun } from '../../types';
import { api } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import './EvaluationHistoryPage.css';
import './LocalEvaluationPage.css';

interface EvaluationHistoryPageProps {
  onNewEvaluation: () => void;
}

export const EvaluationHistoryPage: React.FC<EvaluationHistoryPageProps> = ({
  onNewEvaluation,
}) => {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<EvaluationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        setLoading(true);
        const data = await api.getEvaluationRuns();
        setRuns(data);
        if (data.length > 0) {
          setSelectedRun(data[0]);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load evaluation history');
      } finally {
        setLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const handleExportJson = () => {
    if (!selectedRun) return;
    const blob = new Blob([JSON.stringify(selectedRun, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evalforge20-run-${selectedRun.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="page-container loading-state">
        <span className="spinner" />
        <p>Loading persisted evaluation history...</p>
      </div>
    );
  }

  return (
    <div className="page-container history-page-container">
      {/* Header */}
      <div className="history-header-bar">
        <div>
          <h1 className="history-header-title">Evaluation History</h1>
          <p className="history-header-subtitle">
            Audit trail of all benchmark executions, exact test cases, latency measurements, and pass rates.
          </p>
        </div>
        <Button variant="primary" size="sm" onClick={onNewEvaluation}>
          + Run New Evaluation
        </Button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {runs.length === 0 ? (
        <div className="empty-state">
          <h3>No evaluations recorded in database yet</h3>
          <p>Run your first benchmark against a local Ollama model or catalog double.</p>
          <Button variant="primary" onClick={onNewEvaluation} style={{ marginTop: '14px' }}>
            Launch First Local Evaluation
          </Button>
        </div>
      ) : (
        <div className="history-layout-grid">
          {/* Runs Sidebar List */}
          <div className="history-sidebar">
            <h2 className="history-section-title">
              Historical Runs ({runs.length})
            </h2>
            <div className="history-runs-list">
              {runs.map((r) => {
                const isSelected = selectedRun?.id === r.id;
                const passRate = ((r.metrics?.pass_rate || 0) * 100).toFixed(0);
                return (
                  <div
                    key={r.id}
                    onClick={() => setSelectedRun(r)}
                    className={`history-run-card ${isSelected ? 'selected' : ''}`}
                  >
                    <div className="run-card-header">
                      <span className="run-model-name font-mono">
                        {r.model_id}
                      </span>
                      <Badge variant={r.status === 'completed' ? 'success' : 'error'}>
                        {passRate}%
                      </Badge>
                    </div>
                    <p className="run-benchmark-name">
                      {r.benchmark_name}
                    </p>
                    <div className="run-card-footer font-mono">
                      <span>{r.metrics?.total_cases || 0} cases</span>
                      <span>{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Run Detail Inspection */}
          <div>
            {selectedRun ? (
              <div className="history-detail-card">
                <div className="detail-top-bar">
                  <div className="detail-title-group">
                    <h3>{selectedRun.benchmark_name}</h3>
                    <p className="detail-meta-text font-mono">
                      Run ID: {selectedRun.id} &bull; Executed at: {new Date(selectedRun.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={handleExportJson}>
                    Export JSON
                  </Button>
                </div>

                {/* Score Summary Metrics */}
                <div className="metrics-stats-row">
                  <div className="stat-metric-card">
                    <span className="metric-card-label">Pass Rate</span>
                    <span className="metric-card-val accent font-mono">
                      {((selectedRun.metrics.pass_rate || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="stat-metric-card">
                    <span className="metric-card-label">Cases Passed</span>
                    <span className="metric-card-val font-mono">
                      {selectedRun.metrics.passed_cases || 0} / {selectedRun.metrics.total_cases || 0}
                    </span>
                  </div>
                  <div className="stat-metric-card">
                    <span className="metric-card-label">Mean Latency</span>
                    <span className="metric-card-val font-mono">
                      {selectedRun.metrics.avg_latency_ms ? `${selectedRun.metrics.avg_latency_ms.toFixed(0)}ms` : 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Case Assertions */}
                <div>
                  <div className="assertions-section-title">
                    Case Results ({selectedRun.case_results.length})
                  </div>
                  <div className="assertions-table-wrapper">
                    <table className="assertions-table">
                      <thead>
                        <tr>
                          <th>Status</th>
                          <th>Case ID</th>
                          <th>Prompt</th>
                          <th>Expected</th>
                          <th>Actual</th>
                          <th>Latency</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedRun.case_results.map((c) => (
                          <tr key={c.case_id}>
                            <td>
                              <Badge variant={c.passed ? 'success' : 'error'}>
                                {c.passed ? 'PASS' : 'FAIL'}
                              </Badge>
                            </td>
                            <td className="font-mono" style={{ color: 'var(--text-muted)' }}>{c.case_id}</td>
                            <td style={{ color: 'var(--text-primary)', maxWidth: '240px', wordBreak: 'break-word' }} title={c.prompt}>
                              {c.prompt}
                            </td>
                            <td className="font-mono cell-expected" style={{ maxWidth: '200px', wordBreak: 'break-word' }} title={c.expected_output || undefined}>
                              {c.expected_output}
                            </td>
                            <td className="font-mono cell-actual" style={{ maxWidth: '240px', wordBreak: 'break-word' }} title={c.actual_output || undefined}>
                              {c.actual_output || '<empty>'}
                            </td>
                            <td className="cell-latency font-mono">
                              {c.latency_ms ? `${c.latency_ms.toFixed(0)} ms` : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-detail-box">
                Select a run from the list to view detailed case results.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
