import React, { useState } from 'react';

interface LeaderboardRow {
  rank: number;
  modelName: string;
  score: number;
  latencyMs: number;
  cases: number;
  isLocal: boolean;
}

interface LeaderboardTableProps {
  rows: LeaderboardRow[];
}

export const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ rows }) => {
  const [filter, setFilter] = useState('');

  const filtered = rows.filter((r) =>
    r.modelName.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-white/5 space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-semibold text-[#F5F0E7]">Model Leaderboard Ranking</h4>
        <input
          type="text"
          placeholder="Filter model..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-1 bg-[#161715] border border-white/10 rounded-xl text-xs text-[#F5F0E7] focus:outline-none focus:border-[#D9823B]"
        />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-white/10 text-[#A7A29A]">
              <th className="py-2">Rank</th>
              <th className="py-2">Model</th>
              <th className="py-2">Score</th>
              <th className="py-2">Latency</th>
              <th className="py-2">Cases</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.map((r) => (
              <tr key={r.modelName} className="hover:bg-white/[0.02]">
                <td className="py-2.5 font-mono text-[#D9823B]">#{r.rank}</td>
                <td className="py-2.5 text-[#F5F0E7] font-medium flex items-center gap-1.5">
                  {r.modelName}
                  {r.isLocal && <span className="px-1.5 py-0.2 rounded text-[10px] bg-[#68B587]/20 text-[#68B587]">Local</span>}
                </td>
                <td className="py-2.5 font-mono font-semibold text-[#68B587]">{r.score.toFixed(1)}%</td>
                <td className="py-2.5 font-mono text-[#A7A29A]">{r.latencyMs}ms</td>
                <td className="py-2.5 font-mono text-[#A7A29A]">{r.cases}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
