import React, { useState } from 'react';
import {
  ChevronUp,
  ChevronDown,
  Terminal,
  CheckCircle2,
  XCircle,
  Download,
} from 'lucide-react';
import { Button } from '../ui/Primitives';

interface ResultsPanelProps {
  isEvaluating: boolean;
  progressPercentage: number;
  completedSteps: number;
  totalSteps: number;
  logs: string[];
  cases: Array<{
    case_index: number;
    prompt: string;
    expected_output?: string;
    actual_output: string;
    passed: boolean;
    latency_ms: number;
    evaluators?: Record<string, any>;
    error_message?: string;
  }>;
  onExportJson?: () => void;
  onExportCsv?: () => void;
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({
  isEvaluating,
  progressPercentage,
  completedSteps,
  totalSteps,
  logs,
  cases,
  onExportJson,
  onExportCsv,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState<'cases' | 'logs'>('cases');
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed'>('all');

  const filteredCases = cases.filter((c) => {
    if (filter === 'passed') return c.passed;
    if (filter === 'failed') return !c.passed;
    return true;
  });

  const passedCount = cases.filter((c) => c.passed).length;
  const passRate = cases.length > 0 ? (passedCount / cases.length) * 100 : 0;

  return (
    <div
      className={`bg-white border-t border-[#E2E8F0] shadow-lg flex flex-col transition-all z-20 ${
        isExpanded ? 'h-72' : 'h-10'
      }`}
    >
      {/* PANEL HEADER */}
      <div className="h-10 px-4 bg-[#F8FAFC] border-b border-[#E2E8F0] flex items-center justify-between select-none shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1.5 text-xs font-semibold text-[#111827] hover:text-[#2563EB]"
          >
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            <span>Evaluation Results & Live Logs</span>
          </button>

          {isEvaluating && (
            <div className="flex items-center gap-2">
              <div className="w-32 bg-[#E2E8F0] rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-[#2563EB] h-full transition-all duration-300"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <span className="text-[11px] font-mono text-[#64748B]">
                {completedSteps}/{totalSteps} ({progressPercentage.toFixed(0)}%)
              </span>
            </div>
          )}

          {cases.length > 0 && !isEvaluating && (
            <div className="flex items-center gap-2 text-xs">
              <span className="text-[11px] font-semibold text-[#16A34A] bg-[#F0FDF4] px-2 py-0.5 rounded border border-[#BBF7D0]">
                Pass Rate: {passRate.toFixed(1)}% ({passedCount}/{cases.length})
              </span>
            </div>
          )}
        </div>

        {isExpanded && (
          <div className="flex items-center gap-2">
            <div className="flex rounded-md border border-[#E2E8F0] bg-white p-0.5">
              <button
                onClick={() => setActiveTab('cases')}
                className={`px-2.5 py-1 text-xs font-medium rounded ${
                  activeTab === 'cases' ? 'bg-[#EFF6FF] text-[#2563EB]' : 'text-[#64748B]'
                }`}
              >
                Cases ({cases.length})
              </button>
              <button
                onClick={() => setActiveTab('logs')}
                className={`px-2.5 py-1 text-xs font-medium rounded flex items-center gap-1.5 ${
                  activeTab === 'logs' ? 'bg-[#EFF6FF] text-[#2563EB]' : 'text-[#64748B]'
                }`}
              >
                <Terminal className="w-3 h-3" />
                Logs ({logs.length})
              </button>
            </div>

            {activeTab === 'cases' && (
              <div className="flex rounded-md border border-[#E2E8F0] bg-white p-0.5 text-[11px]">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-2 py-0.5 rounded ${filter === 'all' ? 'bg-[#F1F5F9] font-bold text-[#111827]' : 'text-[#64748B]'}`}
                >
                  All
                </button>
                <button
                  onClick={() => setFilter('passed')}
                  className={`px-2 py-0.5 rounded ${filter === 'passed' ? 'bg-[#F0FDF4] font-bold text-[#16A34A]' : 'text-[#64748B]'}`}
                >
                  Passed
                </button>
                <button
                  onClick={() => setFilter('failed')}
                  className={`px-2 py-0.5 rounded ${filter === 'failed' ? 'bg-[#FEF2F2] font-bold text-[#DC2626]' : 'text-[#64748B]'}`}
                >
                  Failed
                </button>
              </div>
            )}

            {onExportCsv && (
              <Button variant="outline" size="sm" onClick={onExportCsv} icon={<Download className="w-3 h-3" />}>
                CSV
              </Button>
            )}
            {onExportJson && (
              <Button variant="outline" size="sm" onClick={onExportJson} icon={<Download className="w-3 h-3" />}>
                JSON
              </Button>
            )}
          </div>
        )}
      </div>

      {/* PANEL BODY */}
      {isExpanded && (
        <div className="flex-1 overflow-auto p-3 text-xs bg-white">
          {activeTab === 'cases' ? (
            cases.length === 0 ? (
              <div className="h-full flex items-center justify-center text-center text-[#94A3B8]">
                Connect a Model, Dataset, and Evaluator, then click Evaluate to see live results.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-[#E2E8F0] text-[11px] font-semibold text-[#64748B] bg-[#F8FAFC]">
                      <th className="py-1.5 px-2">#</th>
                      <th className="py-1.5 px-2">Status</th>
                      <th className="py-1.5 px-2">Prompt / Input</th>
                      <th className="py-1.5 px-2">Actual Output</th>
                      <th className="py-1.5 px-2">Expected Target</th>
                      <th className="py-1.5 px-2">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0] font-mono text-[11px]">
                    {filteredCases.map((c, i) => (
                      <tr key={i} className="hover:bg-[#F8FAFC]">
                        <td className="py-1.5 px-2 text-[#94A3B8]">{c.case_index}</td>
                        <td className="py-1.5 px-2">
                          {c.passed ? (
                            <span className="inline-flex items-center gap-1 text-[#16A34A] font-medium font-sans text-xs">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Pass
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[#DC2626] font-medium font-sans text-xs">
                              <XCircle className="w-3.5 h-3.5" /> Fail
                            </span>
                          )}
                        </td>
                        <td className="py-1.5 px-2 font-sans text-xs text-[#111827] max-w-xs truncate" title={c.prompt}>
                          {c.prompt}
                        </td>
                        <td className="py-1.5 px-2 text-[#111827] max-w-xs truncate" title={c.actual_output}>
                          {c.actual_output || <span className="text-[#94A3B8] italic">(empty)</span>}
                        </td>
                        <td className="py-1.5 px-2 text-[#64748B] max-w-xs truncate" title={c.expected_output}>
                          {c.expected_output || '-'}
                        </td>
                        <td className="py-1.5 px-2 text-[#64748B]">{c.latency_ms.toFixed(0)}ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : (
            <div className="font-mono text-[11px] text-[#334155] space-y-1 bg-[#F8FAFC] p-3 rounded border border-[#E2E8F0] h-full overflow-y-auto">
              {logs.length === 0 ? (
                <div className="text-[#94A3B8]">No execution logs yet.</div>
              ) : (
                logs.map((log, idx) => <div key={idx}>{log}</div>)
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
