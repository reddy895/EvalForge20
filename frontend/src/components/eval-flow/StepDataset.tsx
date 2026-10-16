import React, { useState } from 'react';
import { Database, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';
import type { DatasetValidationReport } from '../../api/types';
import { Button } from '../ui/Button';
import { Textarea } from '../ui/Input';
import { Badge } from '../ui/Badge';
import './StepDataset.css';

interface StepDatasetProps {
  datasetPath: string | null;
  datasetContent: string | null;
  onSelectPath: (path: string | null) => void;
  onSetContent: (content: string | null) => void;
  onValidChange: (isValid: boolean) => void;
}

const PRESET_DATASETS = [
  {
    path: 'examples/datasets/basic.jsonl',
    name: 'basic.jsonl',
    type: 'JSONL',
    cases: 4,
    description: 'Standard multi-domain benchmark covering geography, math, JSON structure, and logic.',
  },
  {
    path: 'examples/datasets/rag_sample.jsonl',
    name: 'rag_sample.jsonl',
    type: 'JSONL (RAG)',
    cases: 3,
    description: 'Reference context retrieval, hallucination detection, and grounded answer synthesis.',
  },
  {
    path: 'examples/datasets/agent_sample.jsonl',
    name: 'agent_sample.jsonl',
    type: 'JSONL (Agent)',
    cases: 2,
    description: 'Autonomous tool invocation traces, argument schemas, and task completion verification.',
  },
];

const DEFAULT_INLINE_JSONL = `{"id": "case_1", "input": "What is the capital of France?", "expected_output": "Paris", "category": "geography"}
{"id": "case_2", "input": "Calculate 128 multiplied by 4.", "expected_output": "512", "category": "math"}`;

export const StepDataset: React.FC<StepDatasetProps> = ({
  datasetPath,
  datasetContent,
  onSelectPath,
  onSetContent,
  onValidChange,
}) => {
  const [mode, setMode] = useState<'preset' | 'custom'>(datasetContent ? 'custom' : 'preset');
  const [rawText, setRawText] = useState<string>(datasetContent || DEFAULT_INLINE_JSONL);
  const [validationReport, setValidationReport] = useState<DatasetValidationReport | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);

  const handleSelectPreset = (path: string) => {
    onSelectPath(path);
    onSetContent(null);
    setValidationReport(null);
    onValidChange(true);
  };

  const handleValidateInline = async () => {
    if (!rawText.trim()) {
      onValidChange(false);
      return;
    }

    setIsValidating(true);
    try {
      const report = await api.validateDataset(rawText);
      setValidationReport(report);
      if (report.is_valid) {
        onSetContent(rawText);
        onSelectPath(null);
        onValidChange(true);
      } else {
        onValidChange(false);
      }
    } catch (err: any) {
      setValidationReport({
        is_valid: false,
        total_lines_read: 0,
        valid_cases_count: 0,
        issues: [{ severity: 'error', message: err.message || 'Validation failed' }],
      });
      onValidChange(false);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="step-dataset">
      <div className="dataset-mode-tabs">
        <button
          type="button"
          className={`dataset-mode-tab ${mode === 'preset' ? 'active' : ''}`}
          onClick={() => {
            setMode('preset');
            if (datasetPath) onValidChange(true);
          }}
        >
          <Database size={13} style={{ display: 'inline', marginRight: '5px' }} />
          Repository Datasets
        </button>
        <button
          type="button"
          className={`dataset-mode-tab ${mode === 'custom' ? 'active' : ''}`}
          onClick={() => {
            setMode('custom');
            onValidChange(validationReport?.is_valid ?? false);
          }}
        >
          <FileText size={13} style={{ display: 'inline', marginRight: '5px' }} />
          Custom Inline JSONL
        </button>
      </div>

      {mode === 'preset' ? (
        <div className="dataset-option-list">
          {PRESET_DATASETS.map((d) => {
            const isSelected = datasetPath === d.path;

            return (
              <div
                key={d.path}
                className={`dataset-option-item ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectPreset(d.path)}
                role="button"
                tabIndex={0}
              >
                <div className="dataset-option-info">
                  <div className="flex-row gap-sm">
                    <span className="dataset-option-name">{d.name}</span>
                    <Badge variant="accent">{d.type}</Badge>
                    <span className="font-mono text-label">{d.cases} test cases</span>
                  </div>
                  <div className="dataset-option-desc">{d.description}</div>
                </div>
                {isSelected && (
                  <CheckCircle2 size={16} color="var(--accent-primary)" />
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="dataset-custom-editor">
          <Textarea
            label="Raw Evaluation Dataset (JSONL format)"
            hint="One complete JSON object per line with required 'id' and 'input' fields."
            isMonospace
            rows={8}
            value={rawText}
            onChange={(e) => {
              setRawText(e.target.value);
              setValidationReport(null);
              onValidChange(false);
            }}
          />
          <div className="flex-between">
            <Button
              variant="secondary"
              size="sm"
              loading={isValidating}
              onClick={handleValidateInline}
            >
              Validate Dataset Schema
            </Button>
            {validationReport && (
              <span className="font-mono" style={{ fontSize: '11px' }}>
                {validationReport.valid_cases_count} valid cases detected
              </span>
            )}
          </div>

          {validationReport && (
            <div
              className={`dataset-validation-box ${
                validationReport.is_valid ? 'valid' : 'invalid'
              }`}
            >
              <div className="flex-row gap-xs" style={{ fontWeight: 600, marginBottom: '4px' }}>
                {validationReport.is_valid ? (
                  <>
                    <CheckCircle2 size={14} />
                    <span>Dataset Validated Successfully</span>
                  </>
                ) : (
                  <>
                    <AlertCircle size={14} />
                    <span>Schema Validation Issues Detected</span>
                  </>
                )}
              </div>
              {validationReport.issues.length > 0 && (
                <ul style={{ paddingLeft: '18px', margin: '4px 0' }}>
                  {validationReport.issues.map((issue, idx) => (
                    <li key={idx}>
                      {issue.line_number && `Line ${issue.line_number}: `}
                      {issue.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
