import React, { useState } from 'react';
import {
  Grid3X3,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Minus,
  Search,
} from 'lucide-react';
import { ModelSummary, TestCaseResult } from '../../types/evaluationResults';

interface TestCasePerformanceMatrixProps {
  modelSummaries: ModelSummary[];
  cases: TestCaseResult[];
  onSelectCase?: (testCase: TestCaseResult) => void;
}

export const TestCasePerformanceMatrix: React.FC<TestCasePerformanceMatrixProps> = ({
  modelSummaries,
  cases,
  onSelectCase,
}) => {
  const [search, setSearch] = useState('');

  if (!cases || cases.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
            <Grid3X3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Per-Test-Case Performance Matrix</h3>
            <p className="text-[11px] text-slate-500">Case-level success, failure, and execution status heatmap</p>
          </div>
        </div>
        <div className="p-8 text-center bg-slate-50 rounded-lg border border-slate-100">
          <p className="text-xs font-medium text-slate-600">No test cases evaluated yet.</p>
        </div>
      </div>
    );
  }

  // Group cases by prompt or case_index
  const uniquePromptsMap = new Map<string, { prompt: string; expected?: string; casesByModel: Record<string, TestCaseResult> }>();

  cases.forEach((c) => {
    const key = c.prompt.trim();
    if (!uniquePromptsMap.has(key)) {
      uniquePromptsMap.set(key, {
        prompt: c.prompt,
        expected: c.expected_output || undefined,
        casesByModel: {},
      });
    }
    uniquePromptsMap.get(key)!.casesByModel[c.model_id] = c;
  });

  const promptEntries = Array.from(uniquePromptsMap.values());
  const filteredPrompts = promptEntries.filter((p) =>
    p.prompt.toLowerCase().includes(search.toLowerCase()) ||
    (p.expected && p.expected.toLowerCase().includes(search.toLowerCase()))
  );

  const models = modelSummaries.map((m) => m.model_id);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs">
      {/* Header and Legend */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
            <Grid3X3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Per-Test-Case Performance Heatmap</h3>
            <p className="text-[11px] text-slate-500">
              Granular comparison of model outcomes across individual test prompts
            </p>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" /> Passed
          </span>
          <span className="flex items-center gap-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
            <XCircle className="w-3.5 h-3.5" /> Failed
          </span>
          <span className="flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" /> Error
          </span>
          <span className="flex items-center gap-1 text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            <Minus className="w-3.5 h-3.5" /> Not evaluated
          </span>
        </div>
      </div>

      {/* Search Input */}
      {promptEntries.length > 5 && (
        <div className="mb-3 relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Filter test cases by prompt keyword..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Heatmap Matrix Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-lg">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-600 font-semibold">
              <th className="py-2.5 px-3 w-12 text-center text-slate-400">#</th>
              <th className="py-2.5 px-3 min-w-[280px]">Test Case Prompt</th>
              {models.map((mId) => (
                <th key={mId} className="py-2.5 px-3 text-center min-w-[130px] font-mono text-[11px]">
                  {mId}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredPrompts.map((entry, index) => (
              <tr key={index} className="hover:bg-slate-50/60 transition-colors">
                <td className="py-2.5 px-3 text-center text-slate-400 font-mono text-[11px]">
                  {index + 1}
                </td>
                <td className="py-2.5 px-3 max-w-md">
                  <div className="font-medium text-slate-800 truncate" title={entry.prompt}>
                    {entry.prompt}
                  </div>
                  {entry.expected && (
                    <div className="text-[11px] text-slate-400 truncate mt-0.5" title={`Expected: ${entry.expected}`}>
                      <span className="text-slate-500 font-medium">Expected:</span> {entry.expected}
                    </div>
                  )}
                </td>
                {models.map((mId) => {
                  const caseItem = entry.casesByModel[mId];
                  if (!caseItem) {
                    return (
                      <td key={mId} className="py-2.5 px-3 text-center">
                        <span className="inline-flex items-center justify-center w-7 h-7 rounded bg-slate-100 text-slate-400">
                          <Minus className="w-3.5 h-3.5" />
                        </span>
                      </td>
                    );
                  }

                  const isError = Boolean(caseItem.error_message);
                  const isPassed = caseItem.passed;

                  let cellStyle = 'bg-rose-50 text-rose-700 border border-rose-200';
                  let Icon = XCircle;
                  let label = 'Failed';

                  if (isError) {
                    cellStyle = 'bg-amber-50 text-amber-800 border border-amber-200';
                    Icon = AlertTriangle;
                    label = 'Error';
                  } else if (isPassed) {
                    cellStyle = 'bg-emerald-50 text-emerald-700 border border-emerald-200';
                    Icon = CheckCircle2;
                    label = 'Passed';
                  }

                  return (
                    <td key={mId} className="py-2.5 px-3 text-center">
                      <button
                        onClick={() => onSelectCase && onSelectCase(caseItem)}
                        title={`${label}${caseItem.latency_ms ? ` (${caseItem.latency_ms}ms)` : ''} — Click to inspect sample`}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium cursor-pointer transition-transform hover:scale-105 ${cellStyle}`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        <span className="font-mono text-[11px]">
                          {caseItem.latency_ms ? `${Math.round(caseItem.latency_ms)}ms` : label}
                        </span>
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
