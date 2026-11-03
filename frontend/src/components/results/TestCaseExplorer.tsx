import React, { useState, useMemo } from 'react';
import {
  ListFilter,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Eye,
  Clock,
  Layers,
} from 'lucide-react';
import { TestCaseResult } from '../../types/evaluationResults';

interface TestCaseExplorerProps {
  cases: TestCaseResult[];
  models: string[];
  evaluators: string[];
  onSelectCase: (testCase: TestCaseResult) => void;
}

export const TestCaseExplorer: React.FC<TestCaseExplorerProps> = ({
  cases,
  models,
  evaluators,
  onSelectCase,
}) => {
  const [statusFilter, setStatusFilter] = useState<'all' | 'passed' | 'failed' | 'skipped'>('all');
  const [modelFilter, setModelFilter] = useState<string>('all');
  const [evaluatorFilter, setEvaluatorFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      // Status filter
      if (statusFilter === 'passed' && !c.passed) return false;
      if (statusFilter === 'failed' && (c.passed || c.error_message)) return false;
      if (statusFilter === 'skipped' && !c.error_message) return false;

      // Model filter
      if (modelFilter !== 'all' && c.model_id !== modelFilter) return false;

      // Evaluator filter
      if (evaluatorFilter !== 'all') {
        const hasEval = c.evaluators && c.evaluators[evaluatorFilter] !== undefined;
        const matchesAssertion = c.assertion_type === evaluatorFilter;
        if (!hasEval && !matchesAssertion) return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const promptMatch = c.prompt.toLowerCase().includes(q);
        const expectedMatch = (c.expected_output || '').toLowerCase().includes(q);
        const actualMatch = (c.actual_output || '').toLowerCase().includes(q);
        const errorMatch = (c.error_message || '').toLowerCase().includes(q);
        if (!promptMatch && !expectedMatch && !actualMatch && !errorMatch) return false;
      }

      return true;
    });
  }, [cases, statusFilter, modelFilter, evaluatorFilter, searchQuery]);

  const passedCount = cases.filter((c) => c.passed).length;
  const failedCount = cases.filter((c) => !c.passed && !c.error_message).length;
  const skippedCount = cases.filter((c) => Boolean(c.error_message)).length;

  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(filteredCases, null, 2));
    const dl = document.createElement('a');
    dl.setAttribute('href', dataStr);
    dl.setAttribute('download', `evalforge-cases-${Date.now()}.json`);
    dl.click();
  };

  const handleExportCsv = () => {
    if (filteredCases.length === 0) return;
    const headers = ['case_id', 'model_id', 'passed', 'latency_ms', 'prompt', 'expected_output', 'actual_output', 'error_message'];
    const rows = filteredCases.map((c) => [
      c.case_id,
      c.model_id,
      c.passed,
      c.latency_ms ?? '',
      `"${(c.prompt || '').replace(/"/g, '""')}"`,
      `"${(c.expected_output || '').replace(/"/g, '""')}"`,
      `"${(c.actual_output || '').replace(/"/g, '""')}"`,
      `"${(c.error_message || '').replace(/"/g, '""')}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const dl = document.createElement('a');
    dl.setAttribute('href', encodeURI(csvContent));
    dl.setAttribute('download', `evalforge-cases-${Date.now()}.csv`);
    dl.click();
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
      {/* Title & Export */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <ListFilter className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Individual Test-Case Explorer</h3>
            <p className="text-[11px] text-slate-500">
              Audit granular prompts, model outputs, evaluator scores, and execution evidence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportJson}
            disabled={filteredCases.length === 0}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Export JSON
          </button>
          <button
            onClick={handleExportCsv}
            disabled={filteredCases.length === 0}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filter Controls Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200/80">
        {/* Status Filters */}
        <div className="flex items-center gap-1 bg-white p-0.5 rounded-lg border border-slate-200">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              statusFilter === 'all'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All ({cases.length})
          </button>
          <button
            onClick={() => setStatusFilter('passed')}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              statusFilter === 'passed'
                ? 'bg-emerald-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Passed ({passedCount})
          </button>
          <button
            onClick={() => setStatusFilter('failed')}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              statusFilter === 'failed'
                ? 'bg-rose-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Failed ({failedCount})
          </button>
          <button
            onClick={() => setStatusFilter('skipped')}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer ${
              statusFilter === 'skipped'
                ? 'bg-amber-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Errors ({skippedCount})
          </button>
        </div>

        {/* Model Filter */}
        {models.length > 1 && (
          <div className="flex items-center gap-1.5 text-xs text-slate-600">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={modelFilter}
              onChange={(e) => setModelFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="all">All Models</option>
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Evaluator Filter */}
        {evaluators.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-slate-600">
            <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={evaluatorFilter}
              onChange={(e) => setEvaluatorFilter(e.target.value)}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1 text-xs font-medium text-slate-800 focus:outline-hidden focus:ring-1 focus:ring-blue-500 cursor-pointer"
            >
              <option value="all">All Evaluators</option>
              {evaluators.map((ev) => (
                <option key={ev} value={ev}>
                  {ev}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Search Input */}
        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search prompt, output, or error text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Test Cases Table */}
      {filteredCases.length === 0 ? (
        <div className="text-center py-10 bg-slate-50 rounded-lg border border-slate-100">
          <p className="text-xs font-medium text-slate-600">No matching test cases found.</p>
          <p className="text-[11px] text-slate-400 mt-0.5">Try resetting the status or search filters.</p>
        </div>
      ) : (
        <div className="overflow-x-auto border border-slate-200 rounded-lg max-h-[480px] overflow-y-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold z-10 shadow-2xs">
              <tr>
                <th className="py-2.5 px-3 w-12 text-center text-slate-400">#</th>
                <th className="py-2.5 px-3 w-28">Status</th>
                <th className="py-2.5 px-3 w-36">Model</th>
                <th className="py-2.5 px-3 min-w-[220px]">Prompt</th>
                <th className="py-2.5 px-3 min-w-[200px]">Model Output</th>
                <th className="py-2.5 px-3 w-24 text-right">Latency</th>
                <th className="py-2.5 px-3 w-20 text-center">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredCases.map((c, idx) => (
                <tr
                  key={`${c.case_id}-${c.model_id}-${idx}`}
                  onClick={() => onSelectCase(c)}
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                >
                  <td className="py-2.5 px-3 text-center text-slate-400 font-mono text-[11px]">
                    {c.case_index || idx + 1}
                  </td>
                  <td className="py-2.5 px-3">
                    {c.error_message ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        <AlertTriangle className="w-3 h-3" /> Error
                      </span>
                    ) : c.passed ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3" /> Passed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                        <XCircle className="w-3 h-3" /> Failed
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[11px] text-slate-700 truncate" title={c.model_id}>
                    {c.model_id}
                  </td>
                  <td className="py-2.5 px-3 max-w-xs">
                    <p className="font-medium text-slate-900 truncate" title={c.prompt}>
                      {c.prompt}
                    </p>
                    {c.expected_output && (
                      <p className="text-[11px] text-slate-400 truncate mt-0.5" title={`Expected: ${c.expected_output}`}>
                        <span className="text-slate-500 font-medium">Exp:</span> {c.expected_output}
                      </p>
                    )}
                  </td>
                  <td className="py-2.5 px-3 max-w-xs">
                    <p className="text-slate-700 truncate font-mono text-[11px]" title={c.actual_output || ''}>
                      {c.actual_output || (c.error_message ? <span className="text-rose-500 italic">Execution Error</span> : <span className="text-slate-400 italic">Empty output</span>)}
                    </p>
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono text-[11px] text-slate-600">
                    {c.latency_ms !== null && c.latency_ms !== undefined ? (
                      <span className="inline-flex items-center gap-1 text-slate-700">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {Math.round(c.latency_ms)}ms
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCase(c);
                      }}
                      className="p-1 rounded text-slate-400 group-hover:text-blue-600 hover:bg-blue-50 transition-colors"
                      title="Inspect full test case details"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
