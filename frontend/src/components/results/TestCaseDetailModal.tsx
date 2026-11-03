import React, { useState, useEffect } from 'react';
import {
  X,
  Copy,
  Check,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Zap,
  Cpu,
  FileCode,
  Tag,
  Hash,
} from 'lucide-react';
import { TestCaseResult } from '../../types/evaluationResults';

interface TestCaseDetailModalProps {
  testCase: TestCaseResult | null;
  onClose: () => void;
}

export const TestCaseDetailModal: React.FC<TestCaseDetailModalProps> = ({
  testCase,
  onClose,
}) => {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!testCase) return null;

  const handleCopy = (text: string, section: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const evaluatorEntries = Object.entries(testCase.evaluators || {});

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 overflow-y-auto animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white rounded-lg border border-slate-200 shadow-xs">
              <FileCode className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="modal-title" className="text-base font-semibold text-slate-900">
                  Test Case Detail
                </h3>
                <span className="font-mono text-xs text-slate-500 bg-slate-200/70 px-2 py-0.5 rounded">
                  {testCase.case_id}
                </span>
                {testCase.case_index !== undefined && (
                  <span className="flex items-center text-xs text-slate-500">
                    <Hash className="w-3 h-3 mr-0.5" />
                    Index {testCase.case_index}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="inline-flex items-center gap-1 text-xs text-slate-600 font-mono">
                  <Cpu className="w-3.5 h-3.5 text-slate-400" />
                  {testCase.model_id}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {testCase.passed ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-4 h-4" /> Passed
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                <XCircle className="w-4 h-4" /> Failed
              </span>
            )}

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 rounded-lg transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Error Banner */}
          {testCase.error_message && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-semibold text-rose-800">Execution Error</h4>
                <p className="text-xs font-mono text-rose-700 mt-1 whitespace-pre-wrap break-words">
                  {testCase.error_message}
                </p>
              </div>
            </div>
          )}

          {/* Telemetry Metrics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                Latency
              </div>
              <div className="text-base font-semibold text-slate-800 font-mono">
                {testCase.latency_ms !== null && testCase.latency_ms !== undefined
                  ? `${testCase.latency_ms.toFixed(1)} ms`
                  : 'N/A'}
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <Zap className="w-3.5 h-3.5 text-slate-400" />
                Throughput
              </div>
              <div className="text-base font-semibold text-slate-800 font-mono">
                {testCase.tokens_per_second !== null && testCase.tokens_per_second !== undefined
                  ? `${testCase.tokens_per_second.toFixed(1)} tok/s`
                  : 'N/A'}
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <Tag className="w-3.5 h-3.5 text-slate-400" />
                Assertion Type
              </div>
              <div className="text-sm font-medium text-slate-800 truncate">
                {testCase.assertion_type || 'Custom Evaluator'}
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
                <Cpu className="w-3.5 h-3.5 text-slate-400" />
                Model Evaluated
              </div>
              <div className="text-sm font-medium text-slate-800 truncate font-mono">
                {testCase.model_id}
              </div>
            </div>
          </div>

          {/* Input Prompt */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Input Prompt
              </label>
              <button
                onClick={() => handleCopy(testCase.prompt, 'prompt')}
                className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800"
              >
                {copiedSection === 'prompt' ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="text-emerald-600">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Prompt</span>
                  </>
                )}
              </button>
            </div>
            <div className="p-3.5 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono whitespace-pre-wrap break-words leading-relaxed max-h-48 overflow-y-auto">
              {testCase.prompt}
            </div>
          </div>

          {/* Outputs: Expected vs Actual */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Expected Output */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Expected Output (Ground Truth)
                </label>
                {testCase.expected_output && (
                  <button
                    onClick={() => handleCopy(testCase.expected_output || '', 'expected')}
                    className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800"
                  >
                    {copiedSection === 'expected' ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="text-emerald-600">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                )}
              </div>
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono whitespace-pre-wrap break-words leading-relaxed text-slate-800 min-h-[120px] max-h-60 overflow-y-auto">
                {testCase.expected_output !== undefined && testCase.expected_output !== null ? (
                  testCase.expected_output
                ) : (
                  <span className="text-slate-400 italic">No expected output provided</span>
                )}
              </div>
            </div>

            {/* Actual Output */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Actual Model Response
                </label>
                {testCase.actual_output && (
                  <button
                    onClick={() => handleCopy(testCase.actual_output || '', 'actual')}
                    className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800"
                  >
                    {copiedSection === 'actual' ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                        <span className="text-emerald-600">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                )}
              </div>
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono whitespace-pre-wrap break-words leading-relaxed text-slate-800 min-h-[120px] max-h-60 overflow-y-auto">
                {testCase.actual_output !== undefined && testCase.actual_output !== null ? (
                  testCase.actual_output
                ) : (
                  <span className="text-slate-400 italic">No output recorded</span>
                )}
              </div>
            </div>
          </div>

          {/* Evaluator Breakdown */}
          {evaluatorEntries.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Evaluator Breakdown
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {evaluatorEntries.map(([evalKey, evalDetail]) => (
                  <div
                    key={evalKey}
                    className="p-3 bg-white border border-slate-200 rounded-lg flex items-start justify-between shadow-xs"
                  >
                    <div>
                      <div className="text-xs font-medium text-slate-900 font-mono">
                        {evalDetail.name || evalKey}
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Method: {evalDetail.method || 'Standard assertion'}
                      </div>
                      {evalDetail.details && (
                        <pre className="text-[10px] text-slate-600 bg-slate-50 p-1.5 rounded mt-1.5 overflow-x-auto max-w-xs">
                          {JSON.stringify(evalDetail.details, null, 2)}
                        </pre>
                      )}
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-sm font-bold text-slate-800 font-mono">
                        {evalDetail.score !== null && evalDetail.score !== undefined
                          ? typeof evalDetail.score === 'number'
                            ? evalDetail.score.toFixed(2)
                            : String(evalDetail.score)
                          : 'N/A'}
                      </div>
                      <span
                        className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold mt-1 ${
                          evalDetail.passed
                            ? 'bg-emerald-50 text-emerald-700'
                            : 'bg-rose-50 text-rose-700'
                        }`}
                      >
                        {evalDetail.passed ? 'PASSED' : 'FAILED'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
