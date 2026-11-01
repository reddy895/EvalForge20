import React, { useEffect, useState } from 'react';
import { Trophy, RefreshCw, Cpu, Award } from 'lucide-react';
import { Badge, EmptyState } from '../components/ui/Primitives';

const CATEGORIES = [
  'Reasoning',
  'Coding',
  'Mathematics',
  'Knowledge',
  'Instruction Following',
  'Performance',
  'Efficiency',
  'Reliability',
  'Safety',
];

export const LeaderboardView: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('Reasoning');
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchLeaderboard = async (cat: string) => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/leaderboard?category=${encodeURIComponent(cat)}`);
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard(selectedCategory);
  }, [selectedCategory]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Domain-Specific Model Leaderboard</h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Empirical local rankings separated by domain. No misleading universal rankings.
          </p>
        </div>
        <button
          onClick={() => fetchLeaderboard(selectedCategory)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#E2E8F0] bg-white text-xs font-medium text-[#64748B] hover:text-[#111827] shadow-sm transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-[#E2E8F0]">
        {CATEGORIES.map((cat) => {
          const isSelected = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                isSelected
                  ? 'bg-[#2563EB] text-white shadow-sm'
                  : 'bg-white text-[#64748B] hover:text-[#111827] border border-[#E2E8F0]'
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Leaderboard Table */}
      {loading ? (
        <div className="text-xs text-[#64748B] py-12 text-center">Loading {selectedCategory} rankings...</div>
      ) : entries.length === 0 ? (
        <EmptyState
          icon={Trophy}
          title={`No evaluation data for ${selectedCategory}`}
          description={`Run benchmarks tagged with ${selectedCategory} in the visual Playground to populate this leaderboard.`}
        />
      ) : (
        <div className="bg-white border border-[#E2E8F0] rounded-lg shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#E2E8F0] text-[11px] font-semibold text-[#64748B] bg-[#F8FAFC]">
                  <th className="py-2.5 px-4 w-12 text-center">Rank</th>
                  <th className="py-2.5 px-4">Model Identifier</th>
                  <th className="py-2.5 px-4">Benchmark / Test</th>
                  <th className="py-2.5 px-4">Primary Metric</th>
                  <th className="py-2.5 px-4 text-right">Score</th>
                  <th className="py-2.5 px-4 text-right">Avg Latency</th>
                  <th className="py-2.5 px-4">Hardware Environment</th>
                  <th className="py-2.5 px-4">Evaluated Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {entries.map((item) => (
                  <tr key={item.rank} className="hover:bg-[#F8FAFC] transition-colors">
                    <td className="py-2.5 px-4 text-center">
                      {item.rank === 1 ? (
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#FEF3C7] text-[#D97706] font-bold text-xs">
                          1
                        </span>
                      ) : item.rank === 2 ? (
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#F1F5F9] text-[#64748B] font-bold text-xs">
                          2
                        </span>
                      ) : item.rank === 3 ? (
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#FFEDD5] text-[#C2410C] font-bold text-xs">
                          3
                        </span>
                      ) : (
                        <span className="font-mono text-[#94A3B8]">{item.rank}</span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 font-semibold text-[#111827]">
                      <div className="flex items-center gap-1.5">
                        <Cpu className="w-3.5 h-3.5 text-[#2563EB]" />
                        <span>{item.model_identifier}</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-4 text-[#64748B]">{item.benchmark_dataset}</td>
                    <td className="py-2.5 px-4 font-mono text-[11px] text-[#64748B]">
                      {item.metric_name}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono font-bold text-[#16A34A] text-sm">
                      {selectedCategory === 'Performance' ? `${item.score.toFixed(0)}ms` : `${(item.score * 100).toFixed(1)}%`}
                    </td>
                    <td className="py-2.5 px-4 text-right font-mono text-[#64748B]">
                      {item.latency_ms ? `${item.latency_ms.toFixed(0)}ms` : '-'}
                    </td>
                    <td className="py-2.5 px-4 text-[11px] text-[#64748B]">{item.hardware}</td>
                    <td className="py-2.5 px-4 font-mono text-[11px] text-[#94A3B8]">
                      {item.evaluated_at}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
