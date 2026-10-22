import React from 'react';
import { CommitAnalytics } from '../types';

interface CommitActivityHeatmapProps {
  data: CommitAnalytics;
}

export const CommitActivityHeatmap: React.FC<CommitActivityHeatmapProps> = ({ data }) => {
  const getLevelColor = (level: number) => {
    switch (level) {
      case 4: return 'bg-[#68B587] text-[#191A18]';
      case 3: return 'bg-[#68B587]/75 text-white';
      case 2: return 'bg-[#68B587]/45 text-white';
      case 1: return 'bg-[#68B587]/20 text-[#68B587]';
      default: return 'bg-white/5 text-[#A7A29A]';
    }
  };

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7]">Repository Activity & Verification</h4>
          <p className="text-xs text-[#A7A29A]">Milestone target: {data.target_commits} verified commits</p>
        </div>
        <div className="px-3 py-1 rounded-full text-xs font-mono font-medium bg-[#68B587]/15 text-[#68B587] border border-[#68B587]/20 self-start sm:self-auto">
          {data.total_verified_commits} Verified Commits ({data.target_progress_percent}% achieved)
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
        {data.daily_activity.map((day) => (
          <div key={day.date} className={`p-3 rounded-2xl border border-white/10 ${getLevelColor(day.level)} flex flex-col items-center justify-center`}>
            <span className="text-[11px] font-mono opacity-80">{day.date.slice(5)}</span>
            <span className="text-base font-mono font-bold mt-1">{day.count}</span>
            <span className="text-[10px] opacity-75">commits</span>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-[#A7A29A] text-right font-mono">Source: {data.source}</p>
    </div>
  );
};
