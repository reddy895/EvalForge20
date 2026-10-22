import React from 'react';

interface CapabilityDimension {
  name: string;
  value: number;
}

interface NormalizedRadarChartProps {
  modelName: string;
  dimensions: CapabilityDimension[];
}

export const NormalizedRadarChart: React.FC<NormalizedRadarChartProps> = ({
  modelName,
  dimensions,
}) => {
  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-semibold text-[#F5F0E7]">{modelName} — Capability Profile</h4>
        <span className="text-xs text-[#A7A29A]">Normalized 0-100</span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {dimensions.map((d) => (
          <div key={d.name} className="p-3 bg-[#161715] rounded-2xl border border-white/5">
            <p className="text-[11px] text-[#A7A29A]">{d.name}</p>
            <p className="text-base font-mono font-bold text-[#D9823B] mt-1">{d.value}%</p>
          </div>
        ))}
      </div>
    </div>
  );
};
