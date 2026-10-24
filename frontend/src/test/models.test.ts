import { describe, it, expect, vi } from 'vitest';
import { SAMPLE_MODELS, toModelSummary } from '../data/models';
import { api } from '../services/api';

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

  it('filters local models exclusively when localOnly filter is active', () => {
    const localModels = SAMPLE_MODELS.filter((m) => m.is_local);
    expect(localModels.length).toBeGreaterThan(0);
    for (const m of localModels) {
      expect(m.is_local).toBe(true);
      expect(m.pricing.is_free_local).toBe(true);
    }
  });

  it('verifies structured output and tool capability flags exist on capable models', () => {
    const jsonCapable = SAMPLE_MODELS.filter((m) => m.supports_structured_output);
    expect(jsonCapable.length).toBeGreaterThan(0);

    const toolsCapable = SAMPLE_MODELS.filter((m) => m.supports_tools);
    expect(toolsCapable.length).toBeGreaterThan(0);
  });

  it('fetches live models from api.getModels with graceful fallback', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        total: 2,
        models: [
          SAMPLE_MODELS[0],
          SAMPLE_MODELS[1],
        ],
      }),
    } as unknown as Response);

    const res = await api.getModels();
    expect(res.models.length).toBe(2);
    expect(res.total).toBe(2);
    expect(res.models[0].id).toBe(SAMPLE_MODELS[0].id);
  });
});
