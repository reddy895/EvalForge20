import React from 'react';
import { ShieldCheck } from 'lucide-react';

export interface QualityData {
  modelName: string;
  accuracy: number;
  passedCount: number;
  totalCount: number;
  benchmarkSuite?: string;
}

export interface AccuracyQualityChartProps {
  data: QualityData[];
  title?: string;
  description?: string;
}

/**
 * Chart 2: Model Accuracy Comparison
 * Clean minimal 2D horizontal bar chart comparing pass rate percentages (0–100%)
 * across evaluated models under comparable benchmark conditions.
 */
export const AccuracyQualityChart: React.FC<AccuracyQualityChartProps> = ({
  data,
  title = 'Model Accuracy Comparison',
  description = 'Pass rate percentage (0–100%) across evaluated test cases',
}) => {
  // Exclude invalid or incomplete results (e.g. totalCount <= 0 or NaN accuracy)
  const validRecords = (data || [])
    .filter(
      (item) =>
        item &&
        typeof item.accuracy === 'number' &&
        !isNaN(item.accuracy) &&
        typeof item.totalCount === 'number' &&
        item.totalCount > 0
    )
    .map((item) => ({
      ...item,
      accuracy: Math.min(100, Math.max(0, item.accuracy)),
    }))
    // Sort consistently: highest accuracy first
    .sort((a, b) => b.accuracy - a.accuracy);

  if (validRecords.length === 0) {
    return (
      <div className="p-8 bg-[#1F201D] rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center space-y-3 min-h-[260px]">
        <div className="w-10 h-10 rounded-2xl bg-[#68B587]/10 text-[#68B587] flex items-center justify-center">
          <ShieldCheck size={20} />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-[#F5F0E7]">{title}</h4>
          <p className="text-xs text-[#A7A29A] max-w-sm">
            No valid accuracy records available. Run an evaluation suite to verify model pass rates across test assertions.
          </p>
        </div>
      </div>
    );
  }

  // 0–100% horizontal scale grid ticks
  const ticks = [0, 25, 50, 75, 100];

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-6">
      {/* Header and Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <ShieldCheck size={16} className="text-[#68B587]" />
            {title}
          </h4>
          <p className="text-xs text-[#A7A29A] mt-0.5">{description}</p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-[#F5F0E7]">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#68B587]" />
            Pass Rate (0–100%)
          </span>
          <span className="text-[11px] text-[#A7A29A]">(Higher is better)</span>
        </div>
      </div>

      {/* Horizontal 2D Bar Chart Canvas */}
      <div className="space-y-3.5">
        {validRecords.map((item) => {
          const isHigh = item.accuracy >= 85;
          const isMid = item.accuracy >= 65;
          const barColor = isHigh
            ? 'from-[#68B587] to-[#80CFA0]'
            : isMid
            ? 'from-[#D9823B] to-[#E5914C]'
            : 'from-[#E06C75] to-[#E88890]';
          const textColor = isHigh
            ? 'text-[#68B587]'
            : isMid
            ? 'text-[#D9823B]'
            : 'text-[#E06C75]';

          return (
            <div key={item.modelName} className="group relative">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-xs">
                {/* Y-Axis Model Label (Handles long model names) */}
                <div
                  className="sm:w-44 shrink-0 text-[#F5F0E7] font-medium truncate"
                  title={item.modelName}
                >
                  {item.modelName}
                </div>

                {/* Bar Area with Background Track */}
                <div className="flex-1 relative flex items-center h-8 bg-[#161715] rounded-xl px-2 border border-white/5 overflow-hidden">
                  {/* Grid Lines (25%, 50%, 75%) */}
                  <div className="absolute inset-0 flex justify-between pointer-events-none px-2 opacity-15">
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                  </div>

                  {/* Horizontal Bar (0 to 100%) */}
                  <div
                    className={`h-4 bg-gradient-to-r ${barColor} rounded-lg transition-all duration-500 relative group-hover:brightness-110`}
                    style={{ width: `${Math.max(2, item.accuracy)}%` }}
                  />

                  {/* Score & Evaluated Cases count */}
                  <div className="ml-3 flex items-center gap-2 font-mono text-xs z-10 whitespace-nowrap">
                    <span className={`font-bold ${textColor}`}>
                      {item.accuracy.toFixed(1)}%
                    </span>
                    <span className="text-[11px] text-[#A7A29A]">
                      ({item.passedCount}/{item.totalCount} passed)
                    </span>
                  </div>
                </div>
              </div>

              {/* Accessible Hover Tooltip */}
              <div className="hidden group-hover:block absolute left-48 -top-8 z-30 px-3 py-1.5 rounded-xl bg-[#292A26] border border-white/10 text-[11px] font-mono text-[#F5F0E7] shadow-xl pointer-events-none">
                <strong>{item.modelName}</strong>: {item.accuracy.toFixed(1)}% pass rate ({item.passedCount} of {item.totalCount} cases passed)
              </div>
            </div>
          );
        })}
      </div>

      {/* X-Axis Scale & Unit Label */}
      <div className="pt-2 border-t border-white/5 flex flex-col gap-1">
        <div className="flex justify-between text-[10px] font-mono text-[#A7A29A] pl-0 sm:pl-48 pr-2">
          {ticks.map((t) => (
            <span key={t}>{t}%</span>
          ))}
        </div>
        <div className="text-[11px] text-[#78766F] text-center font-mono">
          Horizontal Axis: Pass Rate Percentage (0–100%) — Validated Test Cases
        </div>
      </div>
    </div>
  );
};
