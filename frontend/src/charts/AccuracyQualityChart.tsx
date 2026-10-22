import React from 'react';

interface QualityData {
  modelName: string;
  accuracy: number;
  passedCount: number;
  totalCount: number;
}

interface AccuracyQualityChartProps {
  data: QualityData[];
}

export const AccuracyQualityChart: React.FC<AccuracyQualityChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="p-6 text-center text-[#A7A29A] text-sm">No quality accuracy records available.</div>;
  }

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <h4 className="text-sm font-semibold text-[#F5F0E7]">Deterministic Quality & Accuracy</h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.map((item) => (
          <div key={item.modelName} className="p-4 bg-[#161715] rounded-2xl border border-white/5 flex justify-between items-center">
            <div>
              <p className="text-sm font-semibold text-[#F5F0E7]">{item.modelName}</p>
              <p className="text-xs text-[#A7A29A]">{item.passedCount} of {item.totalCount} cases passed</p>
            </div>
            <span className="text-lg font-mono font-bold text-[#68B587]">{item.accuracy.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};
