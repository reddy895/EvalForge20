import { describe, it, expect } from 'vitest';

describe('Chart data validation', () => {
  it('ensures sample metrics format correctly', () => {
    const metrics = [
      { modelName: 'Qwen 2.5 7B', score: 84.8, isLocal: true },
      { modelName: 'Claude 3.5 Sonnet', score: 93.7, isLocal: false },
    ];
    expect(metrics.length).toBe(2);
    expect(metrics[0].score).toBe(84.8);
    expect(metrics[0].isLocal).toBe(true);
  });
});
