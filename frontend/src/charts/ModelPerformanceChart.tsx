import React from 'react';

interface MetricItem {
  modelName: string;
  score: number;
  isLocal: boolean;
}

interface ModelPerformanceChartProps {
  benchmarkTitle: string;
  metrics: MetricItem[];
}

export const ModelPerformanceChart: React.FC<ModelPerformanceChartProps> = ({
  benchmarkTitle,
  metrics,
}) => {
  if (!metrics || metrics.length === 0) {
    return (
      <div className="p-6 text-center text-[#A7A29A] text-sm bg-[#1F201D] rounded-2xl border border-white/5">
        No evaluation data recorded for {benchmarkTitle}. Run an evaluation to view scores.
      </div>
    );
  }

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-semibold text-[#F5F0E7]">{benchmarkTitle} — Score Comparison</h4>
        <span className="text-xs text-[#A7A29A]">Metric: pass@1 (%)</span>
      </div>
      <div className="space-y-3">
        {metrics.map((m) => (
          <div key={m.modelName} className="space-y-1">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-[#F5F0E7] flex items-center gap-1.5">
                {m.modelName}
                {m.isLocal && <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#68B587]/20 text-[#68B587]">Local</span>}
              </span>
              <span className="text-[#D9823B] font-mono">{m.score.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-[#161715] h-2 rounded-full overflow-hidden">
              <div
                className="bg-[#D9823B] h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, Math.max(0, m.score))}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
