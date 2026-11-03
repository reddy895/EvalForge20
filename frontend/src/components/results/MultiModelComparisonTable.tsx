import React from 'react';
import {
  GitCompare,
  Zap,
  Target,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { ModelSummary, DisagreementItem } from '../../types/evaluationResults';

interface MultiModelComparisonTableProps {
  modelSummaries: ModelSummary[];
  disagreements?: DisagreementItem[];
}

export const MultiModelComparisonTable: React.FC<MultiModelComparisonTableProps> = ({
  modelSummaries,
  disagreements = [],
}) => {
  if (!modelSummaries || modelSummaries.length === 0) {
    return null;
  }

  const isMultiModel = modelSummaries.length > 1;

  // Identify highest accuracy and lowest latency (for highlighting differences without declaring a universal winner)
  const accuracies = modelSummaries.map((m) => m.pass_rate);
  const maxAccuracy = Math.max(...accuracies);

  const validLatencies = modelSummaries
    .map((m) => m.avg_latency_ms)
    .filter((l): l is number => l !== null && l !== undefined && l > 0);
  const minLatency = validLatencies.length > 0 ? Math.min(...validLatencies) : null;

  // Collect all unique evaluator metrics
  const metricKeys = new Set<string>();
  modelSummaries.forEach((m) => {
    Object.keys(m.metrics || {}).forEach((k) => {
      if (!k.startsWith('_') && !['accuracy', 'exact_match'].includes(k)) {
        metricKeys.add(k);
      }
    });
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-6">
      {/* Title */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <GitCompare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              {isMultiModel ? 'Multi-Model Performance Scorecard' : 'Model Evaluation Scorecard'}
            </h3>
            <p className="text-[11px] text-slate-500">
              {isMultiModel
                ? 'Side-by-side evaluation comparison across accuracy, latency, and evaluator metrics'
                : 'Summary of evaluated metrics, throughput, and error rates'}
            </p>
          </div>
        </div>
        {isMultiModel && (
          <span className="text-xs font-semibold px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-200">
            {modelSummaries.length} Models Evaluated
          </span>
        )}
      </div>

      {/* Side-by-side Scorecard Grid / Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {modelSummaries.map((m) => {
          const isHighestAcc = isMultiModel && m.pass_rate === maxAccuracy && maxAccuracy > 0;
          const isLowestLat = isMultiModel && minLatency !== null && m.avg_latency_ms === minLatency;

          return (
            <div
              key={m.model_id}
              className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 flex flex-col justify-between hover:border-slate-300 transition-colors"
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <h4 className="text-xs font-bold font-mono text-slate-900 truncate" title={m.name}>
                      {m.name || m.model_id}
                    </h4>
                    <span className="text-[10px] text-slate-500 font-mono">{m.model_id}</span>
                  </div>

                  <div className="flex flex-col items-end gap-1">
                    {isHighestAcc && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">
                        <Target className="w-3 h-3" /> Highest Accuracy
                      </span>
                    )}
                    {isLowestLat && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded-full">
                        <Zap className="w-3 h-3" /> Lowest Latency
                      </span>
                    )}
                  </div>
                </div>

                {/* Accuracy Bar */}
                <div className="mb-4">
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-xs font-medium text-slate-600">Pass Rate</span>
                    <span className="text-sm font-bold text-slate-900 font-mono">
                      {m.pass_rate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-600 h-full rounded-full transition-all"
                      style={{ width: `${Math.min(100, Math.max(0, m.pass_rate))}%` }}
                    />
                  </div>
                </div>

                {/* Metric Rows */}
                <div className="space-y-2 text-xs border-t border-slate-200/80 pt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      Mean Latency:
                    </span>
                    <span className="font-mono font-semibold text-slate-800">
                      {m.avg_latency_ms !== null && m.avg_latency_ms !== undefined
                        ? `${m.avg_latency_ms} ms`
                        : '—'}
                    </span>
                  </div>

                  {m.median_latency_ms !== undefined && m.median_latency_ms !== null && (
                    <div className="flex justify-between items-center text-[11px]">
                      <span className="text-slate-400">P50 / P95 Latency:</span>
                      <span className="font-mono text-slate-700">
                        {m.median_latency_ms} ms / {m.p95_latency_ms ?? '—'} ms
                      </span>
                    </div>
                  )}

                  <div className="flex justify-between items-center">
                    <span className="text-slate-500 flex items-center gap-1">
                      <Zap className="w-3.5 h-3.5 text-emerald-500" />
                      Throughput:
                    </span>
                    <span className="font-mono font-semibold text-slate-800">
                      {m.tokens_per_second !== null && m.tokens_per_second !== undefined && m.tokens_per_second > 0
                        ? `${m.tokens_per_second} tok/s`
                        : <span className="text-slate-400 font-normal italic">N/A</span>}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Exact Match:</span>
                    <span className="font-mono font-semibold text-slate-800">
                      {m.metrics.exact_match !== null && m.metrics.exact_match !== undefined
                        ? `${(m.metrics.exact_match <= 1.0 ? m.metrics.exact_match * 100 : m.metrics.exact_match).toFixed(1)}%`
                        : <span className="text-slate-400 font-normal italic">N/A</span>}
                    </span>
                  </div>

                  {Array.from(metricKeys).map((k) => (
                    <div key={k} className="flex justify-between items-center">
                      <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}:</span>
                      <span className="font-mono font-semibold text-slate-800">
                        {m.metrics[k] !== null && m.metrics[k] !== undefined
                          ? String(m.metrics[k])
                          : <span className="text-slate-400 font-normal italic">N/A</span>}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom Test Cases Count */}
              <div className="mt-4 pt-3 border-t border-slate-200/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                <span>Passed: <strong className="text-emerald-600">{m.passed_cases}</strong></span>
                <span>Failed: <strong className="text-rose-600">{m.failed_cases}</strong></span>
                <span>Total: <strong>{m.total_cases}</strong></span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Disagreements section when multiple models were evaluated */}
      {isMultiModel && disagreements.length > 0 && (
        <div className="border-t border-slate-200 pt-5 mt-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-amber-500" />
              Per-Test-Case Model Disagreements ({disagreements.length})
            </h4>
            <span className="text-[11px] text-slate-500">
              Prompts where models produced differing evaluation outcomes
            </span>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {disagreements.map((dis, idx) => (
              <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                <div className="font-medium text-slate-800 font-mono">
                  Prompt: <span className="text-slate-900 font-sans font-normal">{dis.prompt}</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                  {Object.entries(dis.results).map(([mId, res]) => (
                    <div
                      key={mId}
                      className={`p-2 rounded border ${
                        res.passed ? 'bg-emerald-50/60 border-emerald-200' : 'bg-rose-50/60 border-rose-200'
                      }`}
                    >
                      <div className="flex items-center justify-between font-mono text-[11px] font-semibold mb-1">
                        <span className="truncate">{mId}</span>
                        <span className={res.passed ? 'text-emerald-700' : 'text-rose-700'}>
                          {res.passed ? 'PASSED' : 'FAILED'}
                        </span>
                      </div>
                      {res.output && (
                        <p className="text-[11px] text-slate-600 truncate" title={res.output}>
                          {res.output}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
