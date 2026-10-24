import React from 'react';
import { Clock, HelpCircle } from 'lucide-react';

export interface LatencyItem {
  modelName: string;
  medianMs: number;
  p95Ms?: number;
  latencyMs?: number;
}

export interface LatencyComparisonChartProps {
  records: LatencyItem[];
  title?: string;
  description?: string;
}

export const LatencyComparisonChart: React.FC<LatencyComparisonChartProps> = ({
  records,
  title = 'Model Performance Comparison',
  description = 'Measured response latency across evaluated models (milliseconds)',
}) => {
  // Exclude invalid, zero, or non-finite latencies
  const validRecords = (records || [])
    .filter(
      (r) =>
        (typeof r.medianMs === 'number' && !isNaN(r.medianMs) && r.medianMs > 0) ||
        (typeof r.latencyMs === 'number' && !isNaN(r.latencyMs) && r.latencyMs > 0)
    )
    .map((r) => ({
      modelName: r.modelName,
      medianMs: typeof r.medianMs === 'number' && r.medianMs > 0 ? r.medianMs : (r.latencyMs || 0),
      p95Ms: typeof r.p95Ms === 'number' && r.p95Ms > 0 ? r.p95Ms : undefined,
    }))
    // Sort consistently: lowest latency (fastest) first
    .sort((a, b) => a.medianMs - b.medianMs);

  if (validRecords.length === 0) {
    return (
      <div className="p-8 bg-[#1F201D] rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center space-y-3 min-h-[260px]">
        <div className="w-10 h-10 rounded-2xl bg-[#D9823B]/10 text-[#D9823B] flex items-center justify-center">
          <Clock size={20} />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-[#F5F0E7]">{title}</h4>
          <p className="text-xs text-[#A7A29A] max-w-sm">
            No valid latency measurements recorded. Run an evaluation against local Ollama or cloud models to view response latency comparisons.
          </p>
        </div>
      </div>
    );
  }

  // Consistent scaling based on highest observed latency
  const rawMax = Math.max(
    ...validRecords.map((r) => (r.p95Ms ? Math.max(r.medianMs, r.p95Ms) : r.medianMs))
  );
  // Round up to clean ceiling
  const maxVal = Math.max(50, Math.ceil(rawMax * 1.15));

  // Clean 4-segment minimal grid ticks
  const ticks = [0, Math.round(maxVal * 0.33), Math.round(maxVal * 0.66), maxVal];

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-6">
      {/* Header and Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <Clock size={16} className="text-[#D9823B]" />
            {title}
          </h4>
          <p className="text-xs text-[#A7A29A] mt-0.5">{description}</p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-[#F5F0E7]">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#D9823B]" />
            Median (ms)
          </span>
          <span className="text-[11px] text-[#A7A29A]">(Lower is better)</span>
        </div>
      </div>

      {/* Horizontal 2D Bar Chart Canvas */}
      <div className="space-y-3.5">
        {validRecords.map((r) => {
          const barWidth = Math.min(100, Math.max(2, (r.medianMs / maxVal) * 100));

          return (
            <div key={r.modelName} className="group relative">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-xs">
                {/* Y-Axis Model Label (Handles long model names gracefully) */}
                <div
                  className="sm:w-44 shrink-0 text-[#F5F0E7] font-medium truncate"
                  title={r.modelName}
                >
                  {r.modelName}
                </div>

                {/* Bar Area with Background Track */}
                <div className="flex-1 relative flex items-center h-7 bg-[#161715] rounded-xl px-2 border border-white/5 overflow-hidden">
                  {/* Subtle Grid Tick Marks */}
                  <div className="absolute inset-0 flex justify-between pointer-events-none px-2 opacity-15">
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                  </div>

                  {/* Horizontal Bar */}
                  <div
                    className="h-3.5 bg-gradient-to-r from-[#D9823B] to-[#E5914C] rounded-lg transition-all duration-500 relative group-hover:brightness-110"
                    style={{ width: `${barWidth}%` }}
                  />

                  {/* Numeric Value at end of bar */}
                  <span className="ml-3 font-mono text-xs font-bold text-[#F5F0E7] whitespace-nowrap z-10">
                    {r.medianMs.toFixed(1)} <span className="text-[10px] text-[#A7A29A] font-normal">ms</span>
                  </span>
                </div>
              </div>

              {/* Accessible Hover Tooltip */}
              <div className="hidden group-hover:block absolute left-48 -top-8 z-30 px-3 py-1.5 rounded-xl bg-[#292A26] border border-white/10 text-[11px] font-mono text-[#F5F0E7] shadow-xl pointer-events-none">
                <strong>{r.modelName}</strong>: {r.medianMs.toFixed(1)}ms median latency
                {r.p95Ms && <span className="text-[#A7A29A]"> • P95: {r.p95Ms.toFixed(1)}ms</span>}
              </div>
            </div>
          );
        })}
      </div>

      {/* X-Axis Scale & Unit Label */}
      <div className="pt-2 border-t border-white/5 flex flex-col gap-1">
        <div className="flex justify-between text-[10px] font-mono text-[#A7A29A] pl-0 sm:pl-48 pr-2">
          {ticks.map((t, idx) => (
            <span key={idx}>{t} ms</span>
          ))}
        </div>
        <div className="text-[11px] text-[#78766F] text-center font-mono">
          Horizontal Axis: Measured Latency (ms) — Consistent 2D Linear Scale
        </div>
      </div>
    </div>
  );
};
