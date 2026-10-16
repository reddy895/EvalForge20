import React, { useState } from 'react';
import { CheckCircle2, AlertCircle, Upload } from 'lucide-react';
import { api } from '../../api/client';
import type { DatasetValidationReport } from '../../api/types';
import { useToast } from '../../context/ToastContext';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input, Textarea } from '../ui/Input';

interface ImportDatasetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const TEMPLATE_SAMPLE = `{"id": "eval_1", "input": "Explain quantum superposition in simple terms.", "expected_output": "Quantum particles can exist in multiple states at once until measured.", "category": "physics"}
{"id": "eval_2", "input": "Write a Python function to reverse a list.", "expected_output": "def reverse_list(lst): return lst[::-1]", "category": "coding"}`;

export const ImportDatasetModal: React.FC<ImportDatasetModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const toast = useToast();
  const [filename, setFilename] = useState<string>('custom_eval_dataset.jsonl');
  const [content, setContent] = useState<string>(TEMPLATE_SAMPLE);
  const [validationReport, setValidationReport] = useState<DatasetValidationReport | null>(null);
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [isImporting, setIsImporting] = useState<boolean>(false);

  const handleValidate = async () => {
    if (!content.trim()) return;
    setIsValidating(true);
    try {
      const report = await api.validateDataset(content);
      setValidationReport(report);
      if (report.is_valid) {
        toast.success(
          `Dataset validated: ${report.valid_cases_count} cases detected.`,
          'Validation Passed'
        );
      } else {
        toast.warning(
          `Validation failed with ${report.issues.length} issues.`,
          'Check Schema'
        );
      }
    } catch (err: any) {
      toast.error(err.message || 'Validation request failed');
    } finally {
      setIsValidating(false);
    }
  };

  const handleImport = async () => {
    if (!filename.trim() || !content.trim()) return;
    setIsImporting(true);
    try {
      const res = await fetch('/v1/datasets/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, content }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.message || 'Failed to import dataset');
      }

      toast.success(`Dataset "${filename}" imported successfully!`, 'Import Complete');
      onSuccess();
      onClose();
    } catch (err: any) {
      toast.error(err.message || 'Import error', 'Import Failed');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Import Evaluation Dataset"
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="secondary"
            loading={isValidating}
            onClick={handleValidate}
          >
            Validate Syntax
          </Button>
          <Button
            variant="primary"
            iconLeft={<Upload size={13} />}
            loading={isImporting}
            disabled={!filename.trim() || !content.trim()}
            onClick={handleImport}
          >
            Import & Save
          </Button>
        </>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        <Input
          label="Dataset Filename"
          required
          isMonospace
          value={filename}
          onChange={(e) => setFilename(e.target.value)}
          hint="Files are saved in data/ directory. Must end in .jsonl, .json, or .csv"
        />

        <Textarea
          label="Dataset Content"
          required
          isMonospace
          rows={10}
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            setValidationReport(null);
          }}
          hint="Provide JSONL lines with 'id' and 'input' properties."
        />

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
                  <span>
                    Validation Passed: {validationReport.valid_cases_count} valid cases
                  </span>
                </>
              ) : (
                <>
                  <AlertCircle size={14} />
                  <span>Schema Validation Issues</span>
                </>
              )}
            </div>
            {validationReport.issues.length > 0 && (
              <ul style={{ paddingLeft: '18px', margin: '4px 0', fontSize: '11px' }}>
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
    </Modal>
  );
};
