import React from 'react';

interface TrendPoint {
  date: string;
  passRate: number;
  latencyMs: number;
}

interface HistoricalTrendsChartProps {
  points: TrendPoint[];
}

export const HistoricalTrendsChart: React.FC<HistoricalTrendsChartProps> = ({ points }) => {
  if (!points || points.length === 0) {
    return <div className="p-6 text-center text-[#A7A29A] text-sm">No historical trend points available.</div>;
  }

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <h4 className="text-sm font-semibold text-[#F5F0E7]">Historical Performance Trends</h4>
      <div className="space-y-2">
        {points.map((pt, i) => (
          <div key={i} className="flex justify-between items-center text-xs p-2.5 bg-[#161715] rounded-xl font-mono">
            <span className="text-[#A7A29A]">{pt.date}</span>
            <span className="text-[#68B587] font-semibold">{pt.passRate.toFixed(1)}% pass</span>
            <span className="text-[#D9823B]">{pt.latencyMs}ms</span>
          </div>
        ))}
      </div>
    </div>
  );
};
