import React from 'react';
import { LeaderboardTable } from '../charts/LeaderboardTable';

export const LeaderboardView: React.FC = () => {
  const sampleLeaderboard = [
    { rank: 1, modelName: 'Qwen 2.5 7B Instruct', score: 84.8, latencyMs: 142, cases: 48, isLocal: true },
    { rank: 2, modelName: 'Claude 3.5 Sonnet', score: 93.7, latencyMs: 280, cases: 48, isLocal: false },
    { rank: 3, modelName: 'Llama 3.1 8B Instruct', score: 72.4, latencyMs: 165, cases: 48, isLocal: true },
    { rank: 4, modelName: 'DeepSeek V3', score: 82.6, latencyMs: 240, cases: 48, isLocal: false },
  ];

  return (
    <div className="space-y-6">
      <LeaderboardTable rows={sampleLeaderboard} />
    </div>
  );
};
