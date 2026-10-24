import React from 'react';
import { HelpCircle, Zap } from 'lucide-react';

export interface EfficiencyRow {
  modelName: string;
  tokensPerSecond: number | null;
  avgDurationSec: number;
}

export interface EfficiencyMetricsChartProps {
  rows: EfficiencyRow[];
  title?: string;
  description?: string;
}

/**
 * Chart 4: Measured Throughput Comparison
 * Clean minimal horizontal 2D bar chart for measured generation tokens per second (tok/s).
 * Clearly explains when a provider does not expose token generation metadata.
 */
export const EfficiencyMetricsChart: React.FC<EfficiencyMetricsChartProps> = ({
  rows,
  title = 'Throughput Comparison',
  description = 'Measured generation throughput in tokens per second (tok/s)',
}) => {
  if (!rows || rows.length === 0) {
    return (
      <div className="p-8 bg-[#1F201D] rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center space-y-3 min-h-[260px]">
        <div className="w-10 h-10 rounded-2xl bg-[#68B587]/10 text-[#68B587] flex items-center justify-center">
          <Zap size={20} />
        </div>
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-[#F5F0E7]">{title}</h4>
          <p className="text-xs text-[#A7A29A] max-w-sm">
            No token throughput data available. Run an evaluation where response token counts are captured.
          </p>
        </div>
      </div>
    );
  }

  // Find max valid tokens per second for consistent horizontal scaling
  const validValues = rows
    .map((r) => r.tokensPerSecond)
    .filter((v): v is number => typeof v === 'number' && !isNaN(v) && v > 0);

  const maxTokPerSec = validValues.length > 0 ? Math.max(...validValues) : 50;
  const ceiling = Math.max(20, Math.ceil(maxTokPerSec * 1.2));
  const ticks = [0, Math.round(ceiling * 0.33), Math.round(ceiling * 0.66), ceiling];

  // Sort: valid throughput models first (descending), then unmeasured models
  const sortedRows = [...rows].sort((a, b) => {
    const valA = a.tokensPerSecond ?? -1;
    const valB = b.tokensPerSecond ?? -1;
    return valB - valA;
  });

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-6">
      {/* Header and Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <Zap size={16} className="text-[#68B587]" />
            {title}
          </h4>
          <p className="text-xs text-[#A7A29A] mt-0.5">{description}</p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-[#68B587]">
            <span className="w-2.5 h-2.5 rounded-sm bg-[#68B587]" /> Measured Throughput
          </span>
          <span className="text-[11px] text-[#A7A29A]">(Higher is faster)</span>
        </div>
      </div>

      {/* Horizontal Bar Chart Rows */}
      <div className="space-y-3.5">
        {sortedRows.map((row) => {
          const hasValidThroughput =
            typeof row.tokensPerSecond === 'number' &&
            !isNaN(row.tokensPerSecond) &&
            row.tokensPerSecond > 0;

          const barWidth = hasValidThroughput
            ? Math.min(100, Math.max(3, (row.tokensPerSecond! / ceiling) * 100))
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

                  {hasValidThroughput ? (
                    <>
                      <div
                        className="h-4 bg-gradient-to-r from-[#68B587] to-[#8CD5AA] rounded-lg transition-all duration-500 relative group-hover:brightness-110"
                        style={{ width: `${barWidth}%` }}
                      />
                      <div className="ml-3 flex items-center gap-2 font-mono text-xs z-10 whitespace-nowrap">
                        <span className="font-bold text-[#68B587]">
                          {row.tokensPerSecond!.toFixed(1)} <span className="text-[10px] text-[#A7A29A] font-normal">tok/s</span>
                        </span>
                        <span className="text-[10px] text-[#A7A29A]">
                          ({row.avgDurationSec.toFixed(2)}s duration)
                        </span>
                      </div>
                    </>
                  ) : (
                    <div className="flex items-center gap-1.5 text-[11px] text-[#A7A29A] font-mono z-10 px-1">
                      <HelpCircle size={12} className="text-[#D9823B]" />
                      <span>N/A — Provider does not expose token generation metadata</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Accessible Hover Tooltip */}
              <div className="hidden group-hover:block absolute left-48 -top-8 z-30 px-3 py-1.5 rounded-xl bg-[#292A26] border border-white/10 text-[11px] font-mono text-[#F5F0E7] shadow-xl pointer-events-none">
                <strong>{row.modelName}</strong>:{' '}
                {hasValidThroughput
                  ? `${row.tokensPerSecond!.toFixed(1)} tok/s (${row.avgDurationSec.toFixed(2)}s avg generation time)`
                  : 'Tokens per second measurement unavailable from this adapter'}
              </div>
            </div>
          );
        })}
      </div>

      {/* X-Axis Scale & Unit Label */}
      <div className="pt-2 border-t border-white/5 flex flex-col gap-1">
        <div className="flex justify-between text-[10px] font-mono text-[#A7A29A] pl-0 sm:pl-48 pr-2">
          {ticks.map((t, idx) => (
            <span key={idx}>{t} tok/s</span>
          ))}
        </div>
        <div className="text-[11px] text-[#78766F] text-center font-mono">
          Horizontal Axis: Generation Throughput (Tokens / Second)
        </div>
      </div>
    </div>
  );
};
