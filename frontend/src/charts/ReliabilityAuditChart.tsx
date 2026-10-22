import React from 'react';

interface ReliabilityAuditChartProps {
  completedRuns: number;
  failedRuns: number;
  timeoutRuns: number;
  reliabilityRate: number;
}

export const ReliabilityAuditChart: React.FC<ReliabilityAuditChartProps> = ({
  completedRuns,
  failedRuns,
  timeoutRuns,
  reliabilityRate,
}) => {
  const total = completedRuns + failedRuns + timeoutRuns;

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-semibold text-[#F5F0E7]">Inference Reliability & Execution Rate</h4>
        <span className="text-sm font-mono font-bold text-[#68B587]">{reliabilityRate.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-[#161715] h-3 rounded-full flex overflow-hidden">
        {total > 0 ? (
          <>
            <div style={{ width: `${(completedRuns / total) * 100}%` }} className="bg-[#68B587]" title="Completed" />
            <div style={{ width: `${(failedRuns / total) * 100}%` }} className="bg-red-500" title="Failed" />
            <div style={{ width: `${(timeoutRuns / total) * 100}%` }} className="bg-yellow-500" title="Timeouts" />
          </>
        ) : (
          <div className="w-full bg-white/10" />
        )}
      </div>
      <div className="flex justify-between text-xs text-[#A7A29A] font-mono">
        <span>Completed: {completedRuns}</span>
        <span>Failed: {failedRuns}</span>
        <span>Timeouts: {timeoutRuns}</span>
      </div>
    </div>
  );
};
