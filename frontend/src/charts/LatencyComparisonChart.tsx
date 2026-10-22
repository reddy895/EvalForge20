import React from 'react';
import { Clock } from 'lucide-react';

export interface LatencyItem {
  modelName: string;
  medianMs: number;
  p95Ms: number;
}

export interface LatencyComparisonChartProps {
  records: LatencyItem[];
}

export const LatencyComparisonChart: React.FC<LatencyComparisonChartProps> = ({ records }) => {
  if (!records || records.length === 0) {
    return <div className="p-6 text-center text-[#A7A29A] text-sm">No latency observations recorded.</div>;
  }

  const maxVal = Math.max(...records.map((r) => Math.max(r.medianMs, r.p95Ms)), 50);

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-5">
      <div className="flex justify-between items-center">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <Clock size={16} className="text-[#D9823B]" /> Response Latency Distribution
          </h4>
          <p className="text-xs text-[#A7A29A]">Median (50th percentile) and P95 tail latency comparisons</p>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-[#F5F0E7]">
            <span className="w-2.5 h-2.5 rounded bg-[#F5F0E7]" /> Median
          </span>
          <span className="flex items-center gap-1.5 text-[#D9823B]">
            <span className="w-2.5 h-2.5 rounded bg-[#D9823B]" /> P95
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {records.map((r) => {
          const medianWidth = Math.min(100, (r.medianMs / maxVal) * 100);
          const p95Width = Math.min(100, (r.p95Ms / maxVal) * 100);

          return (
            <div key={r.modelName} className="p-4 bg-[#161715] rounded-2xl border border-white/5 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-medium text-[#F5F0E7]">{r.modelName}</span>
                <div className="flex gap-4 font-mono">
                  <span className="text-[#A7A29A]">
                    Median: <strong className="text-[#F5F0E7]">{r.medianMs}ms</strong>
                  </span>
                  <span className="text-[#A7A29A]">
                    P95: <strong className="text-[#D9823B]">{r.p95Ms}ms</strong>
                  </span>
                </div>
              </div>

              {/* Stacked / Dual Bar */}
              <div className="space-y-1">
                {/* Median Bar */}
                <div className="w-full h-1.5 rounded-full bg-[#242522] overflow-hidden">
                  <div
                    className="h-full bg-[#F5F0E7] rounded-full transition-all duration-500"
                    style={{ width: `${medianWidth}%` }}
                  />
                </div>
                {/* P95 Bar */}
                <div className="w-full h-1.5 rounded-full bg-[#242522] overflow-hidden">
                  <div
                    className="h-full bg-[#D9823B] rounded-full transition-all duration-500"
                    style={{ width: `${p95Width}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
