import React, { useState } from 'react';
import { Copy, Check, FileJson, FileText, Table } from 'lucide-react';
import { api } from '../../api/client';
import type { RunDetailResponse } from '../../api/types';
import { useToast } from '../../context/ToastContext';
import { StatusPill } from '../ui/Badge';
import { Button } from '../ui/Button';
import './RunDetailHeader.css';

interface RunDetailHeaderProps {
  data: RunDetailResponse;
}

export const RunDetailHeader: React.FC<RunDetailHeaderProps> = ({ data }) => {
  const toast = useToast();
  const [copied, setCopied] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<string | null>(null);

  const { run } = data;
  const targetConfig = run.config?.target;
  const datasetPath = run.config?.dataset_path || 'Inline Cases';
  const evaluators = run.config?.evaluators || [];

  const handleCopyId = () => {
    navigator.clipboard.writeText(run.run_id);
    setCopied(true);
    toast.info(`Run ID ${run.run_id} copied to clipboard`);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExport = async (format: 'json' | 'markdown' | 'csv') => {
    setIsExporting(format);
    try {
      const content = await api.getReportText(run.run_id, format);
      const mimeTypes: Record<string, string> = {
        json: 'application/json',
        markdown: 'text/markdown',
        csv: 'text/csv',
      };
      const blob = new Blob([content], { type: mimeTypes[format] || 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `evalforge20-report-${run.run_id}.${format === 'markdown' ? 'md' : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`Exported ${format.toUpperCase()} report successfully`, 'Export Complete');
    } catch (err: any) {
      toast.error(err.message || 'Failed to export evaluation report', 'Export Error');
    } finally {
      setIsExporting(null);
    }
  };

  return (
    <div className="run-detail-header-card">
      <div className="run-detail-top-row">
        <div className="run-detail-title-wrap">
          <div className="run-detail-title">
            <span>{run.name}</span>
            <StatusPill status={run.status} />
          </div>
          <div className="flex-row gap-xs">
            <span className="run-id-pill">
              ID: {run.run_id}
              <button
                type="button"
                className="copy-id-btn"
                onClick={handleCopyId}
                title="Copy Run ID"
                aria-label="Copy Run ID"
              >
                {copied ? <Check size={12} color="var(--status-success)" /> : <Copy size={12} />}
              </button>
            </span>
            {run.error_message && (
              <span style={{ color: 'var(--status-error)', fontSize: '11px' }}>
                Error: {run.error_message}
              </span>
            )}
          </div>
        </div>

        {/* Report Export Buttons */}
        <div className="export-btn-group">
          <Button
            variant="outline"
            size="sm"
            iconLeft={<FileJson size={13} />}
            loading={isExporting === 'json'}
            onClick={() => handleExport('json')}
          >
            Export JSON
          </Button>
          <Button
            variant="outline"
            size="sm"
            iconLeft={<FileText size={13} />}
            loading={isExporting === 'markdown'}
            onClick={() => handleExport('markdown')}
          >
            Export Markdown
          </Button>
          <Button
            variant="outline"
            size="sm"
            iconLeft={<Table size={13} />}
            loading={isExporting === 'csv'}
            onClick={() => handleExport('csv')}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Technical Metadata Grid */}
      <div className="run-detail-meta-grid">
        <div className="meta-field">
          <span className="meta-label">Target Model</span>
          <span className="meta-val">
            {targetConfig?.model_identifier || 'Unknown'} ({targetConfig?.provider_name || 'N/A'})
          </span>
        </div>

        <div className="meta-field">
          <span className="meta-label">Dataset</span>
          <span className="meta-val" title={datasetPath}>
            {datasetPath.split('/').pop()}
          </span>
        </div>

        <div className="meta-field">
          <span className="meta-label">Evaluator Suite</span>
          <span className="meta-val">
            {evaluators.map((e) => e.evaluator_name).join(', ') || 'None'}
          </span>
        </div>

        <div className="meta-field">
          <span className="meta-label">Total Execution Cases</span>
          <span className="meta-val">
            {run.completed_cases} / {run.total_cases} completed
          </span>
        </div>
      </div>
    </div>
  );
};
