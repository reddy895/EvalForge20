import React, { useState } from 'react';

export interface LeaderboardRow {
  rank: number;
  modelName: string;
  score: number;
  latencyMs: number;
  throughput?: number | null;
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
    <div className="p-6 bg-[#1F201D] rounded-3xl border border-[#41413B] space-y-4 shadow-md">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2">
        <div>
          <h4 className="text-sm font-semibold text-[#F5F0E7]">Empirical Model Leaderboard</h4>
          <p className="text-xs text-[#A6A49D]">Ranked by measured pass rate across completed local evaluation runs.</p>
        </div>
        <input
          type="text"
          placeholder="Filter model name..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-3 py-1.5 bg-[#161715] border border-[#41413B] rounded-xl text-xs text-[#F5F0E7] focus:outline-none focus:border-[#D9823B] w-full sm:w-48"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="p-8 text-center text-xs text-[#A6A49D] font-mono border border-dashed border-[#41413B] rounded-2xl">
          {rows.length === 0
            ? 'No evaluation data recorded yet. Execute a test suite in Evaluation Studio to populate this leaderboard.'
            : 'No models matched the search query.'}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#41413B] text-[#A7A29A] font-mono">
                <th className="py-2.5">Rank</th>
                <th className="py-2.5">Model</th>
                <th className="py-2.5">Pass Rate</th>
                <th className="py-2.5">Mean Latency</th>
                <th className="py-2.5">Speed (tok/s)</th>
                <th className="py-2.5">Test Cases</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#41413B]/50">
              {filtered.map((r) => (
                <tr key={`${r.rank}-${r.modelName}`} className="hover:bg-white/[0.02]">
                  <td className="py-3 font-mono text-[#D9823B] font-bold">#{r.rank}</td>
                  <td className="py-3 text-[#F5F0E7] font-medium">
                    <div className="flex items-center gap-2">
                      <span>{r.modelName}</span>
                      {r.isLocal && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-[#68B587]/20 text-[#68B587] font-mono">
                          Ollama
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 font-mono font-semibold text-[#68B587]">{r.score.toFixed(1)}%</td>
                  <td className="py-3 font-mono text-[#F5F0E7]">{r.latencyMs} ms</td>
                  <td className="py-3 font-mono text-[#D9823B]">
                    {r.throughput ? `${r.throughput.toFixed(1)} tok/s` : '—'}
                  </td>
                  <td className="py-3 font-mono text-[#A7A29A]">{r.cases}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
