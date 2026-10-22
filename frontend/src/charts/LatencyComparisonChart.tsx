import React from 'react';

interface LatencyItem {
  modelName: string;
  medianMs: number;
  p95Ms: number;
}

interface LatencyComparisonChartProps {
  records: LatencyItem[];
}

export const LatencyComparisonChart: React.FC<LatencyComparisonChartProps> = ({ records }) => {
  if (!records || records.length === 0) {
    return <div className="p-6 text-center text-[#A7A29A] text-sm">No latency observations recorded.</div>;
  }

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-semibold text-[#F5F0E7]">Response Latency Distribution</h4>
        <span className="text-xs text-[#A7A29A]">Lower is better</span>
      </div>
      <div className="space-y-3">
        {records.map((r) => (
          <div key={r.modelName} className="p-3 bg-[#161715] rounded-2xl flex justify-between items-center">
            <span className="text-xs font-medium text-[#F5F0E7]">{r.modelName}</span>
            <div className="flex gap-4 font-mono text-xs">
              <span className="text-[#A7A29A]">Median: <strong className="text-[#F5F0E7]">{r.medianMs}ms</strong></span>
              <span className="text-[#A7A29A]">P95: <strong className="text-[#D9823B]">{r.p95Ms}ms</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
