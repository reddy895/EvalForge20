import React, { useEffect, useState } from 'react';
import { Plus, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { SearchBar } from '../components/ui/Input';
import { DataTable, type Column } from '../components/ui/DataTable';
import './DatasetsPage.css';

interface DatasetItem {
  name: string;
  path: string;
  format: string;
  size_bytes: number;
  case_count: number;
}

interface DatasetPreviewData {
  filename: string;
  path: string;
  format: string;
  is_valid: boolean;
  total_lines_read: number;
  valid_cases_count: number;
  dataset_hash?: string | null;
  issues: Array<{ line_number?: number; message: string; severity: string }>;
  cases: Array<{
    id: string;
    input: any;
    expected_output?: any;
    category?: string;
    tags?: string[];
    metadata?: Record<string, any>;
  }>;
}

interface DatasetsPageProps {
  onOpenImportModal: () => void;
}

export const DatasetsPage: React.FC<DatasetsPageProps> = ({ onOpenImportModal }) => {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedDataset, setSelectedDataset] = useState<DatasetItem | null>(null);
  const [preview, setPreview] = useState<DatasetPreviewData | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState<boolean>(false);

  const fetchDatasets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listDatasets();
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        handleSelectDataset(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to list evaluation datasets');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectDataset = async (item: DatasetItem) => {
    setSelectedDataset(item);
    setIsLoadingPreview(true);
    try {
      const res = await fetch(`/v1/datasets/preview?path=${encodeURIComponent(item.path)}`);
      if (res.ok) {
        const previewJson = await res.json();
        setPreview(previewJson);
      }
    } catch {
      setPreview(null);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const filteredDatasets = datasets.filter((d) => {
    const q = searchQuery.toLowerCase().trim();
    return !q || d.name.toLowerCase().includes(q) || d.path.toLowerCase().includes(q);
  });

  const columns: Column<DatasetItem>[] = [
    {
      key: 'name',
      header: 'Dataset Name',
      sortable: true,
      render: (d) => (
        <div>
          <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{d.name}</span>
          <div className="font-mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
            {d.path}
          </div>
        </div>
      ),
    },
    {
      key: 'format',
      header: 'Format',
      sortable: true,
      width: '90px',
      render: (d) => <Badge variant="accent">{d.format}</Badge>,
    },
    {
      key: 'case_count',
      header: 'Cases',
      sortable: true,
      align: 'right',
      width: '80px',
      render: (d) => <span className="font-mono tabular-nums">{d.case_count}</span>,
    },
    {
      key: 'size_bytes',
      header: 'File Size',
      sortable: true,
      align: 'right',
      width: '90px',
      render: (d) => (
        <span className="font-mono tabular-nums" style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          {(d.size_bytes / 1024).toFixed(1)} KB
        </span>
      ),
    },
  ];

  return (
    <div className="datasets-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Datasets</h1>
          <p className="page-header-subtitle">
            Manage test cases, inspect JSONL schemas, verify integrity, and import new benchmarks.
          </p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="outline"
            iconLeft={<RefreshCw size={13} />}
            loading={isLoading}
            onClick={fetchDatasets}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            iconLeft={<Plus size={14} />}
            onClick={onOpenImportModal}
            id="btn-import-dataset"
          >
            Import Dataset
          </Button>
        </div>
      </div>

      {error && (
        <div className="toast-item error" role="alert">
          <AlertCircle size={15} className="toast-icon" />
          <div className="toast-content">
            <div className="toast-title">Dataset Query Failed</div>
            <div className="toast-message">{error}</div>
          </div>
        </div>
      )}

      <div className="datasets-grid-layout">
        {/* Left Column: Datasets Browser */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
          <SearchBar
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
            placeholder="Search datasets by name or path..."
          />

          <DataTable
            columns={columns}
            data={filteredDatasets}
            keyExtractor={(d) => d.path}
            isLoading={isLoading}
            onRowClick={(d) => handleSelectDataset(d)}
            emptyMessage="No evaluation dataset files found in repository."
          />
        </div>

        {/* Right Column: Dataset Inspector Panel */}
        <div className="dataset-preview-panel">
          <div className="dataset-preview-header">
            <span className="dataset-preview-title">
              {selectedDataset ? selectedDataset.name : 'Dataset Inspector'}
            </span>
            {preview && (
              <Badge variant={preview.is_valid ? 'success' : 'error'} showDot>
                {preview.is_valid ? 'Validated' : 'Invalid Syntax'}
              </Badge>
            )}
          </div>

          <div className="dataset-preview-body">
            {isLoadingPreview ? (
              <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
                Parsing dataset schema and cases...
              </div>
            ) : preview ? (
              <>
                {/* Metadata Info */}
                <div className="review-summary-card">
                  <div className="review-row">
                    <span className="review-label">Canonical Path</span>
                    <span className="review-value font-mono" style={{ fontSize: '11px' }}>
                      {preview.path}
                    </span>
                  </div>
                  <div className="review-row">
                    <span className="review-label">Version Hash</span>
                    <span className="review-value font-mono" style={{ fontSize: '11px' }}>
                      {preview.dataset_hash ? preview.dataset_hash.substring(0, 16) : 'N/A'}
                    </span>
                  </div>
                  <div className="review-row">
                    <span className="review-label">Validated Test Cases</span>
                    <span className="review-value">
                      {preview.valid_cases_count} of {preview.total_lines_read} lines
                    </span>
                  </div>
                </div>

                {/* Complexity Summary */}
                <div style={{ display: 'flex', gap: 'var(--space-xs)', flexWrap: 'wrap', alignItems: 'center' }}>
                  <span className="text-label" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Complexity:</span>
                  <Badge variant="neutral">
                    Low: {preview.cases.filter((c) => (c.metadata?.complexity || '').toLowerCase() === 'low').length}
                  </Badge>
                  <Badge variant="neutral">
                    Med: {preview.cases.filter((c) => (c.metadata?.complexity || '').toLowerCase() === 'medium').length}
                  </Badge>
                  <Badge variant="accent">
                    High: {preview.cases.filter((c) => (c.metadata?.complexity || '').toLowerCase() === 'high').length}
                  </Badge>
                </div>

                {preview.issues.length > 0 && (
                  <div className="toast-item error">
                    <div className="toast-content">
                      <div className="toast-title">Schema Validation Errors</div>
                      <ul style={{ paddingLeft: '16px', margin: '4px 0', fontSize: '11px' }}>
                        {preview.issues.map((issue, idx) => (
                          <li key={idx}>
                            {issue.line_number && `Line ${issue.line_number}: `}
                            {issue.message}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Test Cases Preview */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                  <div className="flex-between">
                    <span className="text-label">Example Cases Sample</span>
                    <span className="font-mono text-label">{preview.cases.length} displayed</span>
                  </div>

                  {preview.cases.map((c) => (
                    <div key={c.id} className="case-preview-card">
                      <div className="case-preview-header">
                        <span className="font-mono" style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                          ID: {c.id}
                        </span>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          {c.category && <Badge variant="neutral">{c.category}</Badge>}
                          {c.metadata?.complexity && (
                            <Badge variant={c.metadata.complexity.toLowerCase() === 'high' ? 'accent' : 'neutral'}>
                              {c.metadata.complexity}
                            </Badge>
                          )}
                        </div>
                      </div>

                      <div className="case-preview-field">
                        <span className="case-preview-label">Input Prompt:</span>
                        <div className="case-preview-val">
                          {typeof c.input === 'object' ? JSON.stringify(c.input, null, 2) : String(c.input)}
                        </div>
                      </div>

                      {c.expected_output && (
                        <div className="case-preview-field">
                          <span className="case-preview-label">Expected Output:</span>
                          <div className="case-preview-val">
                            {typeof c.expected_output === 'object'
                              ? JSON.stringify(c.expected_output, null, 2)
                              : String(c.expected_output)}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ padding: 'var(--space-xl)', textAlign: 'center', color: 'var(--text-muted)' }}>
                Select a dataset on the left to inspect its test cases and schema structure.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
