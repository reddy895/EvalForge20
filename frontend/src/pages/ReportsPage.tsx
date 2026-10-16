import React, { useEffect, useState } from 'react';
import { FileJson, FileText, Table, Shield, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import type { RunSummary, RunDetailResponse } from '../api/types';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import './ReportsPage.css';

export const ReportsPage: React.FC = () => {
  const toast = useToast();
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [runDetail, setRunDetail] = useState<RunDetailResponse | null>(null);
  const [themeMode, setThemeMode] = useState<'graphite' | 'ivory'>('graphite');
  const [redactInputs, setRedactInputs] = useState<boolean>(false);
  const [redactOutputs, setRedactOutputs] = useState<boolean>(false);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isExporting, setIsExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listEvaluations({ limit: 50 });
      setRuns(data);
      if (data.length > 0 && !selectedRunId) {
        setSelectedRunId(data[0].run_id);
        loadDetail(data[0].run_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to list evaluation runs');
    } finally {
      setIsLoading(false);
    }
  };

  const loadDetail = async (id: string) => {
    try {
      const detail = await api.getEvaluation(id);
      setRunDetail(detail);
    } catch {
      setRunDetail(null);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleRunChange = (id: string) => {
    setSelectedRunId(id);
    loadDetail(id);
  };

  const handleExport = async (format: 'json' | 'markdown' | 'csv') => {
    if (!selectedRunId) return;
    setIsExporting(format);
    try {
      const content = await api.getReportText(
        selectedRunId,
        format,
        redactInputs,
        redactOutputs
      );

      const mimeTypes: Record<string, string> = {
        json: 'application/json',
        markdown: 'text/markdown',
        csv: 'text/csv',
      };
      const blob = new Blob([content], { type: mimeTypes[format] || 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `evalforge20-report-${selectedRunId}.${format === 'markdown' ? 'md' : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success(
        `Generated ${format.toUpperCase()} report successfully!`,
        'Report Exported'
      );
    } catch (err: any) {
      toast.error(err.message || 'Failed to generate report export', 'Export Error');
    } finally {
      setIsExporting(null);
    }
  };

  return (
    <div className="reports-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Evaluation Reports Center</h1>
          <p className="page-header-subtitle">
            Generate and export technical audit summaries in JSON, Markdown, and CSV format.
          </p>
        </div>
      </div>

      {error && (
        <div className="toast-item error" role="alert">
          <AlertCircle size={15} className="toast-icon" />
          <div className="toast-content">
            <div className="toast-title">Unable to Load Reports</div>
            <div className="toast-message">{error}</div>
          </div>
        </div>
      )}

      {/* Report Controls Bar */}
      <div className="report-controls-bar">
        <div className="flex-row gap-sm" style={{ flexWrap: 'wrap' }}>
          <span className="text-label">Target Evaluation Run:</span>
          <select
            className="input-control font-mono"
            style={{ width: '280px' }}
            value={selectedRunId}
            onChange={(e) => handleRunChange(e.target.value)}
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.name} ({r.run_id.substring(0, 10)})
              </option>
            ))}
          </select>

          {/* Privacy Redaction Toggles */}
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '11px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={redactInputs}
              onChange={(e) => setRedactInputs(e.target.checked)}
            />
            <Shield size={12} />
            <span>Redact Prompts</span>
          </label>

          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '11px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={redactOutputs}
              onChange={(e) => setRedactOutputs(e.target.checked)}
            />
            <Shield size={12} />
            <span>Redact Outputs</span>
          </label>
        </div>

        <div className="flex-row gap-sm">
          {/* Surface Theme Switcher */}
          <div className="flex-row gap-xs">
            <button
              type="button"
              className={`case-filter-pill ${themeMode === 'graphite' ? 'active' : ''}`}
              onClick={() => setThemeMode('graphite')}
            >
              Graphite Theme
            </button>
            <button
              type="button"
              className={`case-filter-pill ${themeMode === 'ivory' ? 'active' : ''}`}
              onClick={() => setThemeMode('ivory')}
            >
              Warm Ivory Paper
            </button>
          </div>

          {/* Action Export Buttons */}
          <Button
            variant="secondary"
            size="sm"
            iconLeft={<FileJson size={13} />}
            loading={isExporting === 'json'}
            onClick={() => handleExport('json')}
          >
            Download JSON
          </Button>
          <Button
            variant="secondary"
            size="sm"
            iconLeft={<FileText size={13} />}
            loading={isExporting === 'markdown'}
            onClick={() => handleExport('markdown')}
          >
            Download MD
          </Button>
          <Button
            variant="primary"
            size="sm"
            iconLeft={<Table size={13} />}
            loading={isExporting === 'csv'}
            onClick={() => handleExport('csv')}
          >
            Download CSV
          </Button>
        </div>
      </div>

      {/* Rendered Technical Report Document */}
      {runDetail ? (
        <div className={`report-preview-sheet theme-${themeMode}`}>
          <div className="report-sheet-header">
            <div>
              <div className="report-sheet-title">EVALFORGE20 TECHNICAL AUDIT REPORT</div>
              <div className="report-sheet-sub font-mono">
                RUN ID: {runDetail.run.run_id} · ENGINE: LOCAL FASTAPI/SQLITE · STATUS: {runDetail.run.status.toUpperCase()}
              </div>
            </div>
            <Badge variant="accent">
              Generated: {new Date().toISOString().substring(0, 10)}
            </Badge>
          </div>

          {/* Run Overview Table */}
          <div className="report-table-box">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="data-table-th">Configuration Parameter</th>
                  <th className="data-table-th">Specification</th>
                </tr>
              </thead>
              <tbody>
                <tr className="data-table-tr">
                  <td className="data-table-td" style={{ fontWeight: 600 }}>Evaluation Name</td>
                  <td className="data-table-td font-mono">{runDetail.run.name}</td>
                </tr>
                <tr className="data-table-tr">
                  <td className="data-table-td" style={{ fontWeight: 600 }}>Target Model Identifier</td>
                  <td className="data-table-td font-mono">
                    {runDetail.run.config?.target?.model_identifier || 'mock-model-v1'} (
                    {runDetail.run.config?.target?.provider_name || 'mock'})
                  </td>
                </tr>
                <tr className="data-table-tr">
                  <td className="data-table-td" style={{ fontWeight: 600 }}>Dataset Version Hash</td>
                  <td className="data-table-td font-mono">
                    {runDetail.run.config?.dataset_version_hash || 'inline-hash'}
                  </td>
                </tr>
                <tr className="data-table-tr">
                  <td className="data-table-td" style={{ fontWeight: 600 }}>Total Cases Evaluated</td>
                  <td className="data-table-td font-mono tabular-nums">
                    {runDetail.run.completed_cases} / {runDetail.run.total_cases}
                  </td>
                </tr>
                <tr className="data-table-tr">
                  <td className="data-table-td" style={{ fontWeight: 600 }}>Aggregate Pass Rate</td>
                  <td className="data-table-td font-mono tabular-nums" style={{ fontWeight: 700 }}>
                    {runDetail.aggregates?.pass_rate !== null && runDetail.aggregates?.pass_rate !== undefined
                      ? `${(runDetail.aggregates.pass_rate * 100).toFixed(1)}%`
                      : '—'}
                  </td>
                </tr>
                <tr className="data-table-tr">
                  <td className="data-table-td" style={{ fontWeight: 600 }}>Mean Execution Latency</td>
                  <td className="data-table-td font-mono tabular-nums">
                    {runDetail.aggregates?.mean_latency_ms !== null && runDetail.aggregates?.mean_latency_ms !== undefined
                      ? `${runDetail.aggregates.mean_latency_ms.toFixed(1)} ms`
                      : '—'}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Metric Breakdown Table */}
          {runDetail.aggregates && (
            <div>
              <div className="text-label" style={{ marginBottom: 'var(--space-xs)' }}>
                Evaluator Metric Breakdown
              </div>
              <div className="report-table-box">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th className="data-table-th">Metric Identifier</th>
                      <th className="data-table-th" style={{ textAlign: 'right' }}>Average Score</th>
                      <th className="data-table-th" style={{ textAlign: 'right' }}>Pass Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(runDetail.aggregates.metric_averages || {}).map((mKey) => (
                      <tr key={mKey} className="data-table-tr">
                        <td className="data-table-td font-mono">{mKey}</td>
                        <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                          {(runDetail.aggregates!.metric_averages[mKey] * 100).toFixed(1)}%
                        </td>
                        <td className="data-table-td font-mono tabular-nums" style={{ textAlign: 'right' }}>
                          {runDetail.aggregates!.metric_pass_rates?.[mKey] !== undefined
                            ? `${(runDetail.aggregates!.metric_pass_rates[mKey] * 100).toFixed(1)}%`
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ padding: 'var(--space-2xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
          {isLoading ? 'Loading evaluation report...' : 'No evaluation runs selected.'}
        </div>
      )}
    </div>
  );
};
