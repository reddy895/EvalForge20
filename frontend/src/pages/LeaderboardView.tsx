import React, { useEffect, useState } from 'react';
import { LeaderboardTable, LeaderboardRow } from '../charts/LeaderboardTable';
import { api } from '../services/api';
import { Trophy, RefreshCw } from 'lucide-react';

export const LeaderboardView: React.FC = () => {
  const [rows, setRows] = useState<LeaderboardRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLeaderboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLeaderboard();
      if (Array.isArray(data)) {
        const mapped: LeaderboardRow[] = data.map((item: any, idx: number) => ({
          rank: idx + 1,
          modelName: item.model_name || item.model_id,
          score: Number(((item.pass_rate || 0) * 100).toFixed(1)),
          latencyMs: Number((item.avg_latency_ms || 0).toFixed(1)),
          throughput: item.tokens_per_second ? Number(item.tokens_per_second.toFixed(1)) : null,
          cases: item.total_cases || 0,
          isLocal: item.is_local !== undefined ? item.is_local : true,
        }));
        setRows(mapped);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load leaderboard from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Trophy size={18} className="text-[#D9823B]" />
          <h2 className="text-xl font-bold text-[#F5F0E7]">Empirical Evaluation Leaderboard</h2>
        </div>
        <button
          onClick={fetchLeaderboard}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#242522] border border-[#41413B] text-xs font-mono text-[#A6A49D] hover:text-[#F5F0E7] transition-all cursor-pointer"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-[#E26D5C]/10 border border-[#E26D5C]/40 text-[#E26D5C] text-xs font-mono">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-xs text-[#A6A49D] font-mono bg-[#1F201D] border border-[#41413B] rounded-3xl">
          Loading verified model rankings...
        </div>
      ) : (
        <LeaderboardTable rows={rows} />
      )}
    </div>
  );
};
