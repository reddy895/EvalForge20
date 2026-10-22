import React from 'react';

interface EfficiencyRow {
  modelName: string;
  tokensPerSecond: number | null;
  avgDurationSec: number;
}

interface EfficiencyMetricsChartProps {
  rows: EfficiencyRow[];
}

export const EfficiencyMetricsChart: React.FC<EfficiencyMetricsChartProps> = ({ rows }) => {
  if (!rows || rows.length === 0) {
    return <div className="p-6 text-center text-[#A7A29A] text-sm">No token efficiency data available.</div>;
  }

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <h4 className="text-sm font-semibold text-[#F5F0E7]">Generation Efficiency & Throughput</h4>
      <div className="space-y-2">
        {rows.map((row) => (
          <div key={row.modelName} className="p-3 bg-[#161715] rounded-2xl flex justify-between items-center text-xs">
            <span className="text-[#F5F0E7] font-medium">{row.modelName}</span>
            <div className="flex gap-4 font-mono">
              <span className="text-[#68B587] font-semibold">{row.tokensPerSecond ? `${row.tokensPerSecond} tok/s` : 'N/A (API limited)'}</span>
              <span className="text-[#A7A29A]">{row.avgDurationSec.toFixed(2)}s duration</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
