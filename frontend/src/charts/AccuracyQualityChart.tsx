import React from 'react';
import { CheckCircle2, ShieldCheck } from 'lucide-react';

export interface QualityData {
  modelName: string;
  accuracy: number;
  passedCount: number;
  totalCount: number;
}

export interface AccuracyQualityChartProps {
  data: QualityData[];
}

export const AccuracyQualityChart: React.FC<AccuracyQualityChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="p-6 text-center text-[#A7A29A] text-sm">No quality accuracy records available.</div>;
  }

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-5">
      <div className="flex justify-between items-center">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7] flex items-center gap-2">
            <ShieldCheck size={16} className="text-[#68B587]" /> Deterministic Quality & Accuracy
          </h4>
          <p className="text-xs text-[#A7A29A]">Pass rate percentages across evaluated models</p>
        </div>
        <span className="text-xs font-mono text-[#A7A29A]">Higher is better</span>
      </div>

      <div className="space-y-4">
        {data.map((item) => {
          const isHigh = item.accuracy >= 85;
          const isMid = item.accuracy >= 65;
          const barColor = isHigh ? 'bg-[#68B587]' : isMid ? 'bg-[#D9823B]' : 'bg-[#E06C75]';
          const textColor = isHigh ? 'text-[#68B587]' : isMid ? 'text-[#D9823B]' : 'text-[#E06C75]';

          return (
            <div key={item.modelName} className="p-4 bg-[#161715] rounded-2xl border border-white/5 space-y-2.5">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm font-semibold text-[#F5F0E7]">{item.modelName}</p>
                  <p className="text-xs text-[#A7A29A] flex items-center gap-1 mt-0.5">
                    <CheckCircle2 size={12} className={textColor} />
                    {item.passedCount} of {item.totalCount} cases passed
                  </p>
                </div>
                <div className="text-right">
                  <span className={`text-lg font-mono font-bold ${textColor}`}>
                    {item.accuracy.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Graphical Bar */}
              <div className="w-full h-2 rounded-full bg-[#242522] overflow-hidden">
                <div
                  className={`h-full ${barColor} rounded-full transition-all duration-700`}
                  style={{ width: `${Math.min(100, Math.max(0, item.accuracy))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
