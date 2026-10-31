import React from 'react';
import { Gauge, HelpCircle } from 'lucide-react';

export interface ModelEfficiencyRow {
  modelName: string;
  efficiencyScore: number | null; // e.g. throughput (tok/s) / (latency in sec + 0.1)
  tokensPerSecond: number | null;
  avgLatencyMs: number | null;
}

export interface ModelEfficiencyChartProps {
  rows: ModelEfficiencyRow[];
  title?: string;
  description?: string;
}

/**
 * Chart 4: Model Efficiency Comparison
 * Clean minimal horizontal 2D bar chart for evaluated models showing generation efficiency score.
 * Computed from empirical throughput normalized against execution latency.
 */
export const ModelEfficiencyChart: React.FC<ModelEfficiencyChartProps> = ({
  rows,
  title = 'Model Efficiency Comparison',
  description = 'Generation efficiency index (tok/s normalized by response duration)',
}) => {
  if (!rows || rows.length === 0) {
    return (
      <div className="p-8 bg-[#1F201D] rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center space-y-3 min-h-[260px]">
        <div className="w-10 h-10 rounded-2xl bg-[#0D9488]/10 text-[#14B8A6] flex items-center justify-center">
          <Gauge size={20} />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-[#F5F0E7]">{title}</h4>
          <p className="text-xs text-[#A7A29A] max-w-sm">
            No efficiency metrics available. Run evaluations to compare throughput and latency trade-offs.
          </p>
        </div>
      </div>
    );
  }

  // Find max valid efficiency score for horizontal scaling
  const validScores = rows
    .map((r) => r.efficiencyScore)
    .filter((s): s is number => typeof s === 'number' && !isNaN(s) && s > 0);

  const maxScore = validScores.length > 0 ? Math.max(...validScores) : 20;
  const ceiling = Math.max(10, Math.ceil(maxScore * 1.2));
  const ticks = [0, Math.round(ceiling * 0.33), Math.round(ceiling * 0.66), ceiling];

  // Sort: highest efficiency first
  const sortedRows = [...rows].sort((a, b) => {
    const valA = a.efficiencyScore ?? -1;
    const valB = b.efficiencyScore ?? -1;
    return valB - valA;
  });

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-6">
      {/* Header and Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <Gauge size={16} className="text-[#14B8A6]" />
            {title}
          </h4>
          <p className="text-xs text-[#A7A29A] mt-0.5">{description}</p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-[#14B8A6]">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#0D9488]" /> Efficiency Index
          </span>
          <span className="text-[11px] text-[#A7A29A]">(Higher is more efficient)</span>
        </div>
      </div>

      {/* Horizontal Bar Chart Rows */}
      <div className="space-y-3.5">
        {sortedRows.map((row) => {
          const hasValidScore =
            typeof row.efficiencyScore === 'number' &&
            !isNaN(row.efficiencyScore) &&
            row.efficiencyScore > 0;

          const barWidth = hasValidScore
            ? Math.min(100, Math.max(3, (row.efficiencyScore! / ceiling) * 100))
            : 0;

          return (
            <div key={row.modelName} className="group relative">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-xs">
                {/* Y-Axis Model Label */}
                <div
                  className="sm:w-44 shrink-0 text-[#F5F0E7] font-medium truncate"
                  title={row.modelName}
                >
                  {row.modelName}
                </div>

                {/* Horizontal Bar Area */}
                <div className="flex-1 relative flex items-center h-8 bg-[#161715] rounded-xl px-2 border border-white/5 overflow-hidden">
                  {/* Subtle Grid ticks */}
                  <div className="absolute inset-0 flex justify-between pointer-events-none px-2 opacity-15">
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                    <div className="border-r border-white/40 h-full" />
                  </div>

                  {hasValidScore ? (
                    <>
                      <div
                        className="h-4 bg-[#0D9488] rounded-lg transition-all duration-500 relative group-hover:brightness-110"
                        style={{ width: `${barWidth}%` }}
                      />
                      <div className="ml-3 flex items-center gap-2 font-mono text-xs z-10 whitespace-nowrap">
                        <span className="font-bold text-[#14B8A6]">
                          {row.efficiencyScore!.toFixed(1)} <span className="text-[10px] text-[#A7A29A] font-normal">pts</span>
                        </span>
                        {row.tokensPerSecond && row.avgLatencyMs && (
                          <span className="text-[10px] text-[#A7A29A]">
                            ({row.tokensPerSecond.toFixed(0)} tok/s • {row.avgLatencyMs.toFixed(0)}ms)
                          </span>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="flex items-center gap-1.5 text-[11px] text-[#A7A29A] font-mono z-10 px-1">
                      <HelpCircle size={12} className="text-[#14B8A6]" />
                      <span>N/A — Insufficient execution telemetry</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Hover Tooltip */}
              <div className="hidden group-hover:block absolute left-48 -top-8 z-30 px-3 py-1.5 rounded-xl bg-[#292A26] border border-white/10 text-[11px] font-mono text-[#F5F0E7] shadow-xl pointer-events-none">
                <strong>{row.modelName}</strong>: {hasValidScore ? `${row.efficiencyScore!.toFixed(2)} efficiency index` : 'Unmeasured'}
              </div>
            </div>
          );
        })}
      </div>

      {/* X-Axis Scale & Units */}
      <div className="pt-2 border-t border-white/5 flex flex-col gap-1">
        <div className="flex justify-between text-[10px] font-mono text-[#A7A29A] pl-0 sm:pl-48 pr-2">
          {ticks.map((t) => (
            <span key={t}>{t}</span>
          ))}
        </div>
        <div className="flex justify-between items-center text-[10px] text-[#78766F] pl-0 sm:pl-48 pr-2">
          <span>0 (Low efficiency)</span>
          <span>Normalized Performance Index</span>
          <span>{ceiling}+ (Peak efficiency)</span>
        </div>
      </div>
    </div>
  );
};
