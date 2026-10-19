import { describe, it, expect } from 'vitest';
import { SAMPLE_MODELS, toModelSummary } from '../data/models';

describe('Model Dataset & Intelligence', () => {
  it('contains at least 10 curated models across major families', () => {
    expect(SAMPLE_MODELS.length).toBeGreaterThanOrEqual(10);
  });

  it('verifies that each model has required hardware and benchmark specifications', () => {
    for (const model of SAMPLE_MODELS) {
      expect(model.id).toBeDefined();
      expect(model.name).toBeDefined();
      expect(model.provider).toBeDefined();
      expect(model.context_window).toBeGreaterThan(0);
      if (model.is_local) {
        expect(model.hardware.min_ram_gb).toBeGreaterThan(0);
      } else {
        expect(model.hardware.min_ram_gb).toBeGreaterThanOrEqual(0);
      }
      expect(model.benchmarks.length).toBeGreaterThan(0);
      expect(model.recommended_tasks.length).toBeGreaterThan(0);
    }
  });

  it('correctly maps ModelProfile to ModelSummary', () => {
    const qwen = SAMPLE_MODELS.find((m) => m.id === 'qwen-2.5-7b-instruct')!;
    const summary = toModelSummary(qwen);

    expect(summary.name).toBe(qwen.name);
    expect(summary.is_local).toBe(true);
    expect(summary.headline_benchmark_score).toBe(84.8);
    expect(summary.pricing_summary).toContain('Free (Local)');
  });
});
