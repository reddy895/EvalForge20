import { describe, it, expect } from 'vitest';

describe('Leaderboard sorting logic', () => {
  it('ranks models with highest score first and lowest latency as tie breaker', () => {
    const raw = [
      { name: 'Model B', score: 85, latency: 150 },
      { name: 'Model A', score: 95, latency: 200 },
      { name: 'Model C', score: 85, latency: 120 },
    ];
    const sorted = [...raw].sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return a.latency - b.latency;
    });

    expect(sorted[0].name).toBe('Model A');
    expect(sorted[1].name).toBe('Model C');
    expect(sorted[2].name).toBe('Model B');
  });
});
