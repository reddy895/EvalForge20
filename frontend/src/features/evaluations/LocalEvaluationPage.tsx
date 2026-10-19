import React, { useState, useEffect } from 'react';
import type { ModelCatalogItem, BenchmarkDefinition, EvaluationRun } from '../../types';
import { api } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import './LocalEvaluationPage.css';

interface LocalEvaluationPageProps {
  initialModelId?: string | null;
  onNavigateToHistory?: () => void;
}

export const LocalEvaluationPage: React.FC<LocalEvaluationPageProps> = ({
  initialModelId,
  onNavigateToHistory,
}) => {
  const [models, setModels] = useState<ModelCatalogItem[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkDefinition[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>(initialModelId || '');
  const [selectedBenchmarkId, setSelectedBenchmarkId] = useState<string>('coding_basics');
  const [limit, setLimit] = useState<number>(3);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentRun, setCurrentRun] = useState<EvaluationRun | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [modelsData, benchmarksData] = await Promise.all([
          api.getModels(),
          api.getBenchmarks(),
        ]);
        setModels(modelsData);
        setBenchmarks(benchmarksData);

        if (!selectedModelId && modelsData.length > 0) {
          const localModel = modelsData.find((m) => m.is_local) || modelsData[0];
          setSelectedModelId(localModel.id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load models and benchmarks');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [initialModelId]);

  const handleRunEvaluation = async () => {
    if (!selectedModelId || !selectedBenchmarkId) {
      setError('Please select both a model and a benchmark.');
      return;
    }

    try {
      setRunning(true);
      setError(null);
      const run = await api.runEvaluation({
        model_id: selectedModelId,
        benchmark_id: selectedBenchmarkId,
        limit,
      });
      setCurrentRun(run);
    } catch (err: any) {
      setError(err.message || 'Evaluation failed to complete.');
    } finally {
      setRunning(false);
    }
  };

  const selectedModel = models.find((m) => m.id === selectedModelId);
  const selectedBenchmark = benchmarks.find((b) => b.id === selectedBenchmarkId);

  if (loading) {
    return (
      <div className="page-container loading-state">
        <span className="spinner" />
        <p>Loading evaluation configuration and benchmarks...</p>
      </div>
    );
  }

  return (
    <div className="page-container eval-page-container">
      {/* Header */}
      <div className="eval-header-bar">
        <div>
          <h1 className="eval-header-title">Evaluate Locally</h1>
          <p className="eval-header-subtitle">
            Execute reproducible, deterministic test cases against local Ollama models or verified catalog test-doubles.
          </p>
        </div>
        {onNavigateToHistory && (
          <Button variant="outline" size="sm" onClick={onNavigateToHistory}>
            View Evaluation History &rarr;
          </Button>
        )}
      </div>

      {/* Execution Form Card */}
      <div className="eval-config-card">
        <h2 className="config-card-title">Run Configuration</h2>

        <div className="config-inputs-grid">
          {/* Model Selection */}
          <div className="config-field">
            <label className="field-label">Select Model</label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              disabled={running}
              className="field-select font-mono"
            >
              <optgroup label="Local Models">
                {models
                  .filter((m) => m.is_local)
                  .map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.provider}) [Installed Local]
                    </option>
                  ))}
              </optgroup>
              <optgroup label="Hosted & Catalog Models">
                {models
                  .filter((m) => !m.is_local)
                  .map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.provider})
                    </option>
                  ))}
              </optgroup>
            </select>
            {selectedModel && (
              <div className="field-meta-row">
                <Badge variant={selectedModel.is_local ? 'success' : 'neutral'}>
                  {selectedModel.is_local ? 'Ollama Local' : 'Hosted/Catalog'}
                </Badge>
                <span className="field-helper font-mono">
                  Params: {selectedModel.parameter_count || 'N/A'}
                </span>
              </div>
            )}
          </div>

          {/* Benchmark Selection */}
          <div className="config-field">
            <label className="field-label">Select Benchmark Task</label>
            <select
              value={selectedBenchmarkId}
              onChange={(e) => setSelectedBenchmarkId(e.target.value)}
              disabled={running}
              className="field-select"
            >
              {benchmarks.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.task})
                </option>
              ))}
            </select>
            {selectedBenchmark && (
              <p className="field-helper">{selectedBenchmark.description}</p>
            )}
          </div>

          {/* Test Case Limit */}
          <div className="config-field">
            <label className="field-label">Sample Count (Cases)</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="number"
                min="1"
                max="10"
                value={limit}
                onChange={(e) =>
                  setLimit(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))
                }
                disabled={running}
                className="field-input font-mono"
                style={{ width: '90px' }}
              />
              <span className="field-helper">
                1 to {selectedBenchmark?.total_cases || 5} cases
              </span>
            </div>
            <p className="field-helper">Keeps execution reproducible and responsive.</p>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="config-footer-row">
          <div className="eval-status-message">
            {running ? (
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)' }}>
                <span className="running-pulse" />
                Executing test suite against {selectedModel?.name}...
              </span>
            ) : (
              <span>Ready to execute {limit} test cases with exact verification.</span>
            )}
          </div>
          <Button
            variant="primary"
            onClick={handleRunEvaluation}
            disabled={running || !selectedModelId}
            loading={running}
          >
            {running ? 'Running Evaluation...' : 'Execute Evaluation'}
          </Button>
        </div>
      </div>

      {/* Results View */}
      {currentRun && (
        <div className="eval-results-card">
          <div className="results-top-header">
            <div className="results-title-group">
              <h3>
                {currentRun.benchmark_name} Results
                <Badge variant={currentRun.status === 'completed' ? 'success' : 'error'}>
                  {currentRun.status.toUpperCase()}
                </Badge>
              </h3>
              <div className="results-meta">
                Model: <span className="font-mono" style={{ color: 'var(--text-primary)' }}>{currentRun.model_id}</span> &bull; Run ID: <span className="font-mono">{currentRun.id}</span>
              </div>
            </div>

            {/* Metrics Pills */}
            <div className="metrics-stats-row">
              <div className="stat-metric-card">
                <span className="metric-card-label">Pass Rate</span>
                <span className="metric-card-val accent font-mono">
                  {((currentRun.metrics.pass_rate || 0) * 100).toFixed(0)}%
                </span>
              </div>
              <div className="stat-metric-card">
                <span className="metric-card-label">Passed / Total</span>
                <span className="metric-card-val font-mono">
                  {currentRun.metrics.passed_cases || 0} / {currentRun.metrics.total_cases || 0}
                </span>
              </div>
              <div className="stat-metric-card">
                <span className="metric-card-label">Mean Latency</span>
                <span className="metric-card-val font-mono">
                  {currentRun.metrics.avg_latency_ms ? `${currentRun.metrics.avg_latency_ms.toFixed(0)}ms` : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Test Cases Table */}
          <div>
            <div className="assertions-section-title">Individual Case Assertions</div>
            <div className="assertions-table-wrapper">
              <table className="assertions-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Case ID</th>
                    <th>Prompt</th>
                    <th>Expected Output</th>
                    <th>Actual Response</th>
                    <th>Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {currentRun.case_results.map((c: any) => (
                    <tr key={c.case_id}>
                      <td>
                        <Badge variant={c.passed ? 'success' : 'error'}>
                          {c.passed ? 'PASS' : 'FAIL'}
                        </Badge>
                      </td>
                      <td className="font-mono" style={{ color: 'var(--text-muted)' }}>{c.case_id}</td>
                      <td style={{ color: 'var(--text-primary)', maxWidth: '280px', wordBreak: 'break-word' }} title={c.prompt || undefined}>
                        {c.prompt}
                      </td>
                      <td className="font-mono cell-expected" style={{ maxWidth: '240px', wordBreak: 'break-word' }} title={c.expected_output || undefined}>
                        {c.expected_output}
                      </td>
                      <td className="font-mono cell-actual" style={{ maxWidth: '280px', wordBreak: 'break-word' }} title={c.actual_output || undefined}>
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
      )}
    </div>
  );
};
