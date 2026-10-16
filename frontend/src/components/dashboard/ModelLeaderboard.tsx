import React, { useState, useMemo } from 'react';
import type { RunSummary } from '../../api/types';
import './ModelLeaderboard.css';

interface ModelLeaderboardProps {
  runs: RunSummary[];
  isLoading?: boolean;
}

interface ModelStat {
  model: string;
  evalCount: number;
  avgPassRate: number;
  totalCompletedCases: number;
}

export const ModelLeaderboard: React.FC<ModelLeaderboardProps> = ({ runs, isLoading }) => {
  const [sortBy, setSortBy] = useState<'score' | 'runs'>('score');

  const modelStats = useMemo(() => {
    const map = new Map<string, { totalScore: number; scoreCount: number; runs: number; cases: number }>();

    for (const r of runs) {
      // In EvalForge20 runs, model is either extracted or inferred from run metadata
      const modelName = r.name.includes(':')
        ? r.name.split(':')[0].trim()
        : r.name || 'default-model';

      const existing = map.get(modelName) || { totalScore: 0, scoreCount: 0, runs: 0, cases: 0 };
      existing.runs += 1;
      existing.cases += r.completed_cases || 0;

      if (r.pass_rate !== null && r.pass_rate !== undefined) {
        existing.totalScore += Number(r.pass_rate);
        existing.scoreCount += 1;
      }

      map.set(modelName, existing);
    }

    const list: ModelStat[] = [];
    map.forEach((stat, model) => {
      list.push({
        model,
        evalCount: stat.runs,
        avgPassRate: stat.scoreCount > 0 ? stat.totalScore / stat.scoreCount : 0,
        totalCompletedCases: stat.cases,
      });
    });

    return list.sort((a, b) => {
      if (sortBy === 'score') return b.avgPassRate - a.avgPassRate;
      return b.evalCount - a.evalCount;
    });
  }, [runs, sortBy]);

  if (isLoading) {
    return (
      <div className="leaderboard-card">
        <div className="leaderboard-header">
          <span className="leaderboard-title">Model Leaderboard</span>
        </div>
        <div className="chart-empty-state">
          <span>Computing leaderboard rankings...</span>
        </div>
      </div>
    );
  }

  if (modelStats.length === 0) {
    return (
      <div className="leaderboard-card">
        <div className="leaderboard-header">
          <span className="leaderboard-title">Model Leaderboard</span>
        </div>
        <div className="chart-empty-state">
          <span>No evaluated models recorded in the platform database.</span>
          <span style={{ fontSize: '11px', marginTop: '4px', color: 'var(--text-muted)' }}>
            Execute a new evaluation against Ollama or a mock provider to rank models.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="leaderboard-card">
      <div className="leaderboard-header">
        <span className="leaderboard-title">Model Leaderboard</span>
        <div className="leaderboard-sort-controls">
          <button
            type="button"
            className={`leaderboard-sort-btn ${sortBy === 'score' ? 'active' : ''}`}
            onClick={() => setSortBy('score')}
          >
            Sort by Pass Rate
          </button>
          <button
            type="button"
            className={`leaderboard-sort-btn ${sortBy === 'runs' ? 'active' : ''}`}
            onClick={() => setSortBy('runs')}
          >
            Sort by Runs
          </button>
        </div>
      </div>

      <div className="leaderboard-list">
        {modelStats.map((item, idx) => {
          const rank = idx + 1;
          const scorePercent = (item.avgPassRate * 100).toFixed(1);

          return (
            <div key={item.model} className="leaderboard-row">
              <span className={`leaderboard-rank ${rank === 1 ? 'top-1' : ''}`}>#{rank}</span>
              <span className="leaderboard-model" title={item.model}>
                {item.model}
              </span>
              <div className="leaderboard-bar-track">
                <div
                  className="leaderboard-bar-fill"
                  style={{ width: `${Math.max(3, item.avgPassRate * 100)}%` }}
                />
              </div>
              <span className="leaderboard-score">{scorePercent}%</span>
              <span className="leaderboard-runs-count">{item.evalCount} {item.evalCount === 1 ? 'run' : 'runs'}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
