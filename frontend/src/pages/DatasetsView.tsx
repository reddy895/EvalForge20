import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Database, RefreshCw, Eye, Upload, Plus, Trash2, Copy, ShieldCheck } from 'lucide-react';
import { Badge, EmptyState, Alert, Button } from '../components/ui/Primitives';
import { Input, Select } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { api } from '../services/api';
import type { DatasetItem } from '../types';

interface PreviewCase {
  id: string;
  prompt: string;
  expected_output?: string | null;
  context?: string | null;
  tags?: string[];
}

interface PreviewData {
  dataset_id: string;
  name: string;
  version: number;
  total_cases: number;
  items: PreviewCase[];
}

interface IntegrityData {
  dataset_id: string;
  name: string;
  version: number;
  case_count: number;
  fingerprint: string;
  is_valid: boolean;
  empty_prompts: number;
  duplicate_prompts: number;
  issues: string[];
}

export const DatasetsView: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [integrity, setIntegrity] = useState<IntegrityData | null>(null);

  const [modal, setModal] = useState<'import' | 'create' | null>(null);
  const [busy, setBusy] = useState<boolean>(false);
  const [notice, setNotice] = useState<string | null>(null);

  const [formName, setFormName] = useState<string>('');
  const [formDescription, setFormDescription] = useState<string>('');
  const [formFormat, setFormFormat] = useState<'jsonl' | 'csv'>('jsonl');
  const [formFile, setFormFile] = useState<File | null>(null);
  const [formCases, setFormCases] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);

  const selectedDataset = useMemo(
    () => datasets.find((d) => d.id === selectedId) || null,
    [datasets, selectedId]
  );

  const fetchDatasets = useCallback(async (preferId?: string) => {
    setLoading(true);
    setLoadError(null);
    try {
      const items = await api.getDatasets();
      setDatasets(items);
      setSelectedId((current) => preferId || current || items[0]?.id || null);
    } catch (err: any) {
      setLoadError(err?.message || 'Unable to load datasets from the backend.');
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  useEffect(() => {
    if (!selectedId) {
      setPreview(null);
      setIntegrity(null);
      return;
    }
    let cancelled = false;
    setPreviewLoading(true);
    setPreviewError(null);
    Promise.all([
      api.getDatasetPreview(selectedId, 25),
      api.getDatasetIntegrity(selectedId),
    ])
      .then(([previewData, integrityData]) => {
        if (cancelled) return;
        setPreview(previewData);
        setIntegrity(integrityData);
      })
      .catch((err: any) => {
        if (!cancelled) setPreviewError(err?.message || 'Unable to load dataset preview.');
      })
      .finally(() => {
        if (!cancelled) setPreviewLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const openImport = () => {
    setFormName('');
    setFormDescription('');
    setFormFormat('jsonl');
    setFormFile(null);
    setFormError(null);
    setModal('import');
  };

  const openCreate = () => {
    setFormName('');
    setFormDescription('');
    setFormCases('');
    setFormError(null);
    setModal('create');
  };

  const handleImport = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);
    if (!formName.trim()) {
      setFormError('Dataset name is required.');
      return;
    }
    if (!formFile) {
      setFormError('Choose a JSONL or CSV file to import.');
      return;
    }
    setBusy(true);
    try {
      const result = await api.importDataset({
        name: formName.trim(),
        description: formDescription.trim() || undefined,
        format: formFormat,
        file: formFile,
      });
      const skipped = result.duplicates_skipped
        ? `, ${result.duplicates_skipped} duplicate row(s) skipped`
        : '';
      const failed = result.failed_rows ? `, ${result.failed_rows} row(s) rejected` : '';
      setNotice(`Imported ${result.imported_cases} case(s)${skipped}${failed}.`);
      setModal(null);
      await fetchDatasets(result.dataset_id);
    } catch (err: any) {
      setFormError(err?.message || 'Import failed.');
    } finally {
      setBusy(false);
    }
  };

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);
    if (!formName.trim()) {
      setFormError('Dataset name is required.');
      return;
    }
    const cases = formCases
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line, index) => {
        try {
          const parsed = JSON.parse(line);
          if (!parsed || typeof parsed.prompt !== 'string' || !parsed.prompt.trim()) {
            throw new Error('missing prompt');
          }
          return {
            prompt: parsed.prompt,
            expected_output: parsed.expected_output ?? null,
            context: parsed.context ?? null,
          };
        } catch {
          throw new Error(`Line ${index + 1} is not a valid JSON object with a prompt field.`);
        }
      });
    if (cases.length === 0) {
      setFormError('Add at least one JSONL test case.');
      return;
    }
    setBusy(true);
    try {
      const created = await api.createDataset({
        name: formName.trim(),
        description: formDescription.trim() || undefined,
        cases,
      });
      setNotice(`Created dataset "${created.name}".`);
      setModal(null);
      await fetchDatasets(created.id);
    } catch (err: any) {
      setFormError(err?.message || 'Could not create dataset.');
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedDataset) return;
    if (!window.confirm(`Delete dataset "${selectedDataset.name}" and all its cases?`)) return;
    setBusy(true);
    try {
      await api.deleteDataset(selectedDataset.id);
      setNotice(`Deleted dataset "${selectedDataset.name}".`);
      setSelectedId(null);
      await fetchDatasets();
    } catch (err: any) {
      setLoadError(err?.message || 'Could not delete dataset.');
    } finally {
      setBusy(false);
    }
  };

  const handleDuplicate = async () => {
    if (!selectedDataset) return;
    const name = window.prompt('Name for the duplicated dataset:', `${selectedDataset.name} (copy)`);
    if (!name) return;
    setBusy(true);
    try {
      const clone = await api.duplicateDataset(selectedDataset.id, name);
      setNotice(`Duplicated dataset as "${clone.name}".`);
      await fetchDatasets(clone.id);
    } catch (err: any) {
      setLoadError(err?.message || 'Could not duplicate dataset.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Evaluation Datasets</h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Import, validate, preview, and version benchmark test suites with ground truth.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="md" onClick={() => fetchDatasets()} icon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}>
            Refresh
          </Button>
          <Button variant="outline" size="md" onClick={openCreate} icon={<Plus className="w-3.5 h-3.5" />}>
            New
          </Button>
          <Button variant="primary" size="md" onClick={openImport} icon={<Upload className="w-3.5 h-3.5" />}>
            Import
          </Button>
        </div>
      </div>

      {notice && (
        <Alert type="success" title="Dataset updated">
          {notice}
        </Alert>
      )}
      {loadError && (
        <Alert type="error" title="Backend error">
          {loadError}
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="space-y-3">
          <div className="text-xs font-semibold text-[#111827] uppercase tracking-wider">
            Available Datasets ({datasets.length})
          </div>

          {loading && (
            <div className="space-y-2" aria-live="polite">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-20 rounded-lg bg-[#F1F5F9] animate-pulse" />
              ))}
            </div>
          )}

          {!loading && datasets.length === 0 && !loadError && (
            <EmptyState
              icon={Database}
              title="No datasets yet"
              description="Import a JSONL or CSV file, or create a dataset manually to start evaluating."
              action={
                <Button variant="primary" size="md" onClick={openImport} icon={<Upload className="w-3.5 h-3.5" />}>
                  Import dataset
                </Button>
              }
            />
          )}

          <div className="space-y-2">
            {!loading &&
              datasets.map((d) => {
                const isSelected = selectedId === d.id;
                return (
                  <button
                    type="button"
                    key={d.id}
                    onClick={() => setSelectedId(d.id)}
                    aria-pressed={isSelected}
                    className={`w-full text-left p-3 rounded-lg border cursor-pointer transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] ${
                      isSelected
                        ? 'bg-[#EFF6FF] border-[#2563EB] shadow-sm'
                        : 'bg-white border-[#E2E8F0] hover:border-[#CBD5E1]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="text-xs font-bold text-[#111827] break-words">{d.name}</div>
                      <Badge variant="neutral">v{d.version}</Badge>
                    </div>
                    <div className="text-[11px] text-[#64748B] mt-1 line-clamp-2">
                      {d.description || 'No description provided'}
                    </div>
                    <div className="text-[10px] text-[#64748B] mt-2 font-mono">
                      {d.case_count ?? 0} cases
                    </div>
                  </button>
                );
              })}
          </div>
        </div>

        <div className="md:col-span-2 space-y-4">
          {selectedDataset ? (
            <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm space-y-4">
              <div className="border-b border-[#E2E8F0] pb-3 flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-base font-bold text-[#111827] break-words">{selectedDataset.name}</h2>
                  <p className="text-xs text-[#64748B] mt-0.5">{selectedDataset.description || 'No description provided'}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={handleDuplicate} disabled={busy} icon={<Copy className="w-3.5 h-3.5" />}>
                    Duplicate
                  </Button>
                  <Button variant="danger" size="sm" onClick={handleDelete} disabled={busy} icon={<Trash2 className="w-3.5 h-3.5" />}>
                    Delete
                  </Button>
                </div>
              </div>

              {integrity && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded p-2">
                    <div className="text-[10px] uppercase text-[#64748B]">Cases</div>
                    <div className="text-sm font-semibold text-[#111827]">{integrity.case_count}</div>
                  </div>
                  <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded p-2">
                    <div className="text-[10px] uppercase text-[#64748B]">Valid</div>
                    <div className="text-sm font-semibold text-[#111827]">{integrity.is_valid ? 'Yes' : 'No'}</div>
                  </div>
                  <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded p-2">
                    <div className="text-[10px] uppercase text-[#64748B]">Duplicates</div>
                    <div className="text-sm font-semibold text-[#111827]">{integrity.duplicate_prompts}</div>
                  </div>
                  <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded p-2">
                    <div className="text-[10px] uppercase text-[#64748B]">Empty prompts</div>
                    <div className="text-sm font-semibold text-[#111827]">{integrity.empty_prompts}</div>
                  </div>
                </div>
              )}

              {integrity && (
                <div className="flex items-start gap-1.5 text-[11px] text-[#64748B] font-mono break-all">
                  <ShieldCheck className="w-3.5 h-3.5 shrink-0 mt-0.5 text-[#2563EB]" />
                  <span>SHA-256 {integrity.fingerprint}</span>
                </div>
              )}

              {integrity && integrity.issues.length > 0 && (
                <Alert type="warning" title={`${integrity.issues.length} integrity note(s)`}>
                  <ul className="list-disc pl-4 space-y-0.5">
                    {integrity.issues.slice(0, 5).map((issue) => (
                      <li key={issue}>{issue}</li>
                    ))}
                  </ul>
                </Alert>
              )}

              <div>
                <div className="text-xs font-bold text-[#111827] mb-2 flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-[#2563EB]" />
                  <span>Sample Test Cases</span>
                </div>

                {previewLoading && (
                  <div className="space-y-2" aria-live="polite">
                    <div className="h-16 rounded bg-[#F1F5F9] animate-pulse" />
                    <div className="h-16 rounded bg-[#F1F5F9] animate-pulse" />
                  </div>
                )}
                {previewError && !previewLoading && (
                  <Alert type="error" title="Preview failed">
                    {previewError}
                  </Alert>
                )}
                {!previewLoading && !previewError && preview && preview.items.length === 0 && (
                  <EmptyState
                    icon={Database}
                    title="This dataset has no cases"
                    description="Add test cases before running an evaluation."
                  />
                )}

                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {!previewLoading &&
                    preview?.items.map((sample, idx) => (
                      <div key={sample.id || idx} className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded text-xs space-y-2">
                        <div className="font-semibold text-[#111827] flex items-center justify-between gap-2">
                          <span>Case #{idx + 1}</span>
                          <span className="text-[10px] font-mono text-[#64748B]">{sample.id}</span>
                        </div>
                        <div>
                          <div className="text-[10px] uppercase font-mono text-[#64748B]">Prompt</div>
                          <div className="text-xs text-[#111827] bg-white p-2 rounded border border-[#E2E8F0] mt-0.5 font-mono whitespace-pre-wrap break-words">
                            {sample.prompt}
                          </div>
                        </div>
                        {sample.expected_output && (
                          <div>
                            <div className="text-[10px] uppercase font-mono text-[#64748B]">Expected Output</div>
                            <div className="text-xs text-[#16A34A] bg-[#F0FDF4] p-2 rounded border border-[#BBF7D0] mt-0.5 font-mono whitespace-pre-wrap break-words">
                              {sample.expected_output}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
                {preview && preview.total_cases > preview.items.length && (
                  <p className="text-[11px] text-[#64748B] mt-2">
                    Showing {preview.items.length} of {preview.total_cases} cases.
                  </p>
                )}
              </div>
            </div>
          ) : (
            <EmptyState
              icon={Database}
              title="No Dataset Selected"
              description="Select a dataset to preview its cases, integrity fingerprint, and validation warnings."
            />
          )}
        </div>
      </div>

      <Modal
        isOpen={modal === 'import'}
        onClose={() => setModal(null)}
        title="Import dataset"
        subtitle="JSONL or CSV, UTF-8 encoded"
      >
        <form className="space-y-4" onSubmit={handleImport}>
          <Input
            label="Dataset name"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
            placeholder="My benchmark suite"
            required
          />
          <Input
            label="Description (optional)"
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
            placeholder="What this dataset measures"
          />
          <Select
            label="File format"
            value={formFormat}
            onChange={(e) => setFormFormat(e.target.value as 'jsonl' | 'csv')}
            options={[
              { value: 'jsonl', label: 'JSONL / NDJSON' },
              { value: 'csv', label: 'CSV / TSV' },
            ]}
          />
          <div className="flex flex-col gap-1.5">
            <label htmlFor="dataset-file" className="text-xs font-medium text-[#F5F0E7]/90 tracking-wide">
              Dataset file
            </label>
            <input
              id="dataset-file"
              type="file"
              accept=".jsonl,.ndjson,.csv,.tsv,text/csv,application/jsonl"
              onChange={(e) => setFormFile(e.target.files?.[0] || null)}
              className="text-xs text-[#A6A49D] file:mr-3 file:px-3 file:py-1.5 file:rounded-md file:border-0 file:bg-[#333430] file:text-[#F5F0E7] file:text-xs cursor-pointer"
            />
          </div>
          {formError && <Alert type="error">{formError}</Alert>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="md" onClick={() => setModal(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="md" disabled={busy}>
              {busy ? 'Importing…' : 'Import'}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={modal === 'create'}
        onClose={() => setModal(null)}
        title="Create dataset"
        subtitle="Paste one JSON object per line"
        size="lg"
      >
        <form className="space-y-4" onSubmit={handleCreate}>
          <Input
            label="Dataset name"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
            placeholder="My custom suite"
            required
          />
          <Input
            label="Description (optional)"
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
          />
          <div className="flex flex-col gap-1.5">
            <label htmlFor="dataset-cases" className="text-xs font-medium text-[#F5F0E7]/90 tracking-wide">
              Test cases (JSONL)
            </label>
            <textarea
              id="dataset-cases"
              rows={8}
              value={formCases}
              onChange={(e) => setFormCases(e.target.value)}
              placeholder={'{"prompt": "What is 2+2?", "expected_output": "4"}\n{"prompt": "Reverse abc", "expected_output": "cba"}'}
              className="w-full px-4 py-3 rounded-xl bg-[#191A18] border border-[#41413B] text-[#F5F0E7] placeholder-[#78766F] text-xs font-mono outline-none focus:border-[#D9823B] focus:ring-1 focus:ring-[#D9823B]"
            />
          </div>
          {formError && <Alert type="error">{formError}</Alert>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="md" onClick={() => setModal(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="md" disabled={busy}>
              {busy ? 'Creating…' : 'Create dataset'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
