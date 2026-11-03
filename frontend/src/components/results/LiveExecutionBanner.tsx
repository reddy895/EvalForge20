import React, { useState } from 'react';
import {
  Activity,
  Cpu,
  Clock,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Terminal,
} from 'lucide-react';
import { LiveExecutionProgress } from '../../types/evaluationResults';

interface LiveExecutionBannerProps {
  progress: LiveExecutionProgress;
  isLive: boolean;
}

export const LiveExecutionBanner: React.FC<LiveExecutionBannerProps> = ({
  progress,
  isLive,
}) => {
  const [showLogs, setShowLogs] = useState(false);

  if (!isLive && progress.progress_percentage >= 100 && !progress.error) {
    return null;
  }

  const formatElapsed = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const remainingSecs = sec % 60;
    return `${mins}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-blue-50/80 border-b border-blue-200/90 px-6 py-4 select-none">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Left: Stage info & Model Indicator */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
            <Activity className="w-4 h-4 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-blue-900 tracking-wide uppercase">
                {isLive ? 'Evaluation in Progress' : 'Execution Status'}
              </span>
              {progress.current_model && (
                <span className="inline-flex items-center gap-1 text-[11px] font-mono font-medium px-2 py-0.5 bg-blue-100 text-blue-800 rounded border border-blue-200">
                  <Cpu className="w-3 h-3" />
                  {progress.current_model}
                </span>
              )}
              {progress.current_evaluator && (
                <span className="text-[11px] font-mono px-2 py-0.5 bg-indigo-100 text-indigo-800 rounded border border-indigo-200">
                  {progress.current_evaluator}
                </span>
              )}
            </div>

            <p className="text-xs font-medium text-blue-950 mt-0.5 line-clamp-1">
              {progress.stage}
            </p>
          </div>
        </div>

        {/* Right: Progress Meter & Timer */}
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-blue-950 font-mono">
                {progress.completed_steps}/{progress.total_steps}
              </span>
              <span className="text-xs font-bold text-blue-700 font-mono">
                ({progress.progress_percentage.toFixed(0)}%)
              </span>
            </div>
            <div className="w-44 bg-blue-200/80 rounded-full h-2 mt-1.5 overflow-hidden">
              <div
                className="bg-blue-600 h-full rounded-full transition-all duration-300 ease-out"
                style={{ width: `${Math.min(100, Math.max(0, progress.progress_percentage))}%` }}
              />
            </div>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-white/80 border border-blue-200 rounded-lg text-xs font-mono font-medium text-slate-700 shadow-2xs">
            <Clock className="w-3.5 h-3.5 text-blue-600" />
            <span>{formatElapsed(progress.elapsed_time_seconds)}</span>
          </div>

          {progress.logs.length > 0 && (
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-blue-800 bg-white/80 hover:bg-white border border-blue-200 rounded-lg transition-colors cursor-pointer"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Logs ({progress.logs.length})</span>
              {showLogs ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Error alert if encountered */}
      {progress.error && (
        <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Execution Warning / Error:</div>
            <div className="font-mono mt-0.5">{progress.error}</div>
          </div>
        </div>
      )}

      {/* Expandable Execution Logs */}
      {showLogs && progress.logs.length > 0 && (
        <div className="mt-3 p-3 bg-slate-900 text-slate-200 rounded-xl text-xs font-mono max-h-48 overflow-y-auto space-y-1 shadow-inner">
          <div className="text-[10px] uppercase text-slate-400 font-semibold tracking-wider pb-1 border-b border-slate-800">
            Real-time Streaming Logs
          </div>
          {progress.logs.map((log, idx) => (
            <div key={idx} className="leading-relaxed hover:text-white">
              <span className="text-slate-500 mr-2">[{idx + 1}]</span>
              {log}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
