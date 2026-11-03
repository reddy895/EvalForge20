import React, { useState } from 'react';
import {
  ArrowLeft,
  Copy,
  Check,
  RefreshCw,
  Clock,
  Calendar,
  Layers,
  Database,
  CheckCircle2,
  XCircle,
  StopCircle,
} from 'lucide-react';
import { EvaluationResultsData } from '../../types/evaluationResults';

interface EvaluationSummaryHeaderProps {
  data: EvaluationResultsData;
  isLive?: boolean;
  onBackToPlayground: () => void;
  onRefresh?: () => void;
  onCancel?: () => void;
}

export const EvaluationSummaryHeader: React.FC<EvaluationSummaryHeaderProps> = ({
  data,
  isLive = false,
  onBackToPlayground,
  onRefresh,
  onCancel,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyId = () => {
    navigator.clipboard.writeText(data.execution_id || data.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const status = (data.status || 'PENDING').toUpperCase();
  const isRunning = isLive || status === 'RUNNING' || status === 'PENDING';

  const getStatusBadge = () => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Completed
          </span>
        );
      case 'RUNNING':
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            Live Execution
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <StopCircle className="w-3.5 h-3.5" />
            Cancelled
          </span>
        );
      case 'FAILED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" />
            Failed
          </span>
        );
    }
  };

  const formatDuration = (ms?: number | null) => {
    if (ms === null || ms === undefined || ms <= 0) return '—';
    if (ms < 1000) return `${Math.round(ms)} ms`;
    return `${(ms / 1000).toFixed(2)} s`;
  };

  const formatTimestamp = (iso?: string | null) => {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="bg-white border-b border-slate-200 shadow-xs px-6 py-5 select-none">
      {/* Top Bar: Navigation & Run ID */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToPlayground}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 hover:text-slate-900 rounded-lg transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Playground
          </button>

          <div className="h-4 w-px bg-slate-300" />

          <div>
            <h1 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              {data.name || 'Evaluation Run'}
            </h1>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs font-mono text-slate-500">ID: {data.execution_id || data.id}</span>
              <button
                onClick={handleCopyId}
                title="Copy Run ID"
                className="text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {getStatusBadge()}

          {isRunning && onCancel && (
            <button
              onClick={onCancel}
              className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition-colors cursor-pointer"
            >
              <StopCircle className="w-3.5 h-3.5" />
              Cancel Run
            </button>
          )}

          {onRefresh && (
            <button
              onClick={onRefresh}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Structured Metric Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Model Names */}
        <div className="bg-slate-50/75 rounded-xl p-3 border border-slate-200/80">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            Models ({data.models.length})
          </div>
          <div className="flex flex-wrap gap-1 mt-1 max-h-12 overflow-y-auto">
            {data.models.map((m) => (
              <span
                key={m}
                className="inline-block px-1.5 py-0.5 bg-blue-50 text-blue-700 border border-blue-200/80 rounded text-[11px] font-mono font-medium truncate max-w-full"
                title={m}
              >
                {m}
              </span>
            ))}
          </div>
        </div>

        {/* Dataset */}
        <div className="bg-slate-50/75 rounded-xl p-3 border border-slate-200/80">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-teal-600" />
            Dataset
          </div>
          <div className="text-xs font-semibold text-slate-800 truncate mt-1.5" title={data.dataset_name}>
            {data.dataset_name || 'Standard Benchmark'}
          </div>
        </div>

        {/* Evaluators */}
        <div className="bg-slate-50/75 rounded-xl p-3 border border-slate-200/80">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
            Evaluators ({data.evaluators.length})
          </div>
          <div className="flex flex-wrap gap-1 mt-1 max-h-12 overflow-y-auto">
            {data.evaluators.length > 0 ? (
              data.evaluators.map((ev) => (
                <span
                  key={ev}
                  className="inline-block px-1.5 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-200/80 rounded text-[11px] font-mono font-medium truncate"
                >
                  {ev}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-400">None specified</span>
            )}
          </div>
        </div>

        {/* Test Cases Count */}
        <div className="bg-slate-50/75 rounded-xl p-3 border border-slate-200/80">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Test Cases
          </div>
          <div className="flex items-baseline gap-1.5 mt-1">
            <span className="text-xl font-bold text-slate-900">{data.completed_cases}</span>
            <span className="text-xs font-medium text-slate-500">/ {data.total_cases} completed</span>
          </div>
          <div className="text-[11px] font-medium text-slate-500 mt-0.5">
            Pass Rate: <span className="font-bold text-emerald-600">{data.pass_rate.toFixed(1)}%</span>
          </div>
        </div>

        {/* Failed Cases */}
        <div className="bg-slate-50/75 rounded-xl p-3 border border-slate-200/80">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Outcomes
          </div>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {data.passed_cases} Passed
            </span>
            <span className="text-xs font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
              {data.failed_cases} Failed
            </span>
          </div>
        </div>

        {/* Duration & Timestamp */}
        <div className="bg-slate-50/75 rounded-xl p-3 border border-slate-200/80">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-600" />
            Duration & Time
          </div>
          <div className="text-xs font-semibold text-slate-900 mt-1">
            {formatDuration(data.total_duration_ms)}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
            <Calendar className="w-3 h-3 shrink-0" />
            <span className="truncate">{formatTimestamp(data.created_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
