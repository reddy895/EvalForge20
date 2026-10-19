import React, { useEffect, useState } from 'react';
import { Scale, X, Sparkles, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import type { ModelComparisonResult, ModelSummary } from '../../types';
import { Button } from '../../components/ui/Button';

interface ModelComparisonPageProps {
  selectedModelIds?: string[];
  initialModelIds?: string[];
  onRemoveModel?: (modelId: string) => void;
  onAddModel?: (modelId: string) => void;
  onNavigateToCatalog?: () => void;
}

export const ModelComparisonPage: React.FC<ModelComparisonPageProps> = ({
  selectedModelIds: propSelectedModelIds,
  initialModelIds = [],
  onRemoveModel: propOnRemoveModel,
  onAddModel: propOnAddModel,
  onNavigateToCatalog,
}) => {
  const [internalIds, setInternalIds] = useState<string[]>(
    propSelectedModelIds || initialModelIds.length > 0
      ? (propSelectedModelIds || initialModelIds)
      : ['meta-llama/llama-3.1-8b-instruct', 'qwen/qwen-2.5-7b-instruct']
  );

  const selectedModelIds = propSelectedModelIds || internalIds;

  const handleRemoveModel = (id: string) => {
    if (propOnRemoveModel) {
      propOnRemoveModel(id);
    } else {
      setInternalIds((prev) => prev.filter((m) => m !== id));
    }
  };

  const handleAddModel = (id: string) => {
    if (propOnAddModel) {
      propOnAddModel(id);
    } else {
      setInternalIds((prev) => (prev.includes(id) ? prev : [...prev.slice(0, 3), id]));
    }
  };

  const [availableModels, setAvailableModels] = useState<ModelSummary[]>([]);
  const [comparison, setComparison] = useState<ModelComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load models catalog for picker
  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const list = await api.listModels();
        setAvailableModels(list);
      } catch (e) {
        console.error('Failed to load models list for comparison', e);
      }
    };
    fetchCatalog();
  }, []);

  // Run comparison when selectedModelIds change
  useEffect(() => {
    const fetchComparison = async () => {
      if (selectedModelIds.length < 2) {
        setComparison(null);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const res = await api.compareModels(selectedModelIds);
        setComparison(res);
      } catch (e: any) {
        setError(e.message || 'Failed to compare models');
      } finally {
        setIsLoading(false);
      }
    };

    fetchComparison();
  }, [selectedModelIds]);

  const unselectedModels = availableModels.filter((m) => !selectedModelIds.includes(m.id));

  return (
    <div className="page-container comparison-page">
      <div className="comparison-header">
        <div>
          <h1 className="hero-title">Model Comparison Matrix</h1>
          <p className="hero-subtitle">
            Side-by-side technical evaluation across 2 to 4 AI models. Inspect benchmark scores,
            context window limits, memory footprint, and economics.
          </p>
        </div>

        <Button variant="outline" size="sm" onClick={onNavigateToCatalog}>
          Browse All Models
        </Button>
      </div>

      {/* Selected Models Chips & Quick Adder */}
      <div className="comparison-selector-bar">
        <div className="selected-chips-row">
          <span className="chips-label">Comparing ({selectedModelIds.length}/4):</span>
          {selectedModelIds.map((mid) => {
            const m = availableModels.find((item) => item.id === mid);
            return (
              <span key={mid} className="model-chip">
                <span>{m ? m.name : mid}</span>
                <button
                  className="chip-remove-btn"
                  onClick={() => handleRemoveModel(mid)}
                  aria-label="Remove model"
                >
                  <X size={12} />
                </button>
              </span>
            );
          })}

          {selectedModelIds.length < 4 && unselectedModels.length > 0 && (
            <div className="add-model-picker">
              <select
                className="filter-select"
                onChange={(e) => {
                  if (e.target.value) {
                    handleAddModel(e.target.value);
                    e.target.value = '';
                  }
                }}
                defaultValue=""
              >
                <option value="" disabled>
                  + Add another model...
                </option>
                {unselectedModels.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.provider})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Under 2 Models Callout */}
      {selectedModelIds.length < 2 && (
        <div className="empty-state">
          <Scale size={32} style={{ opacity: 0.5, marginBottom: '8px' }} />
          <h3>Select at least two models to compare</h3>
          <p>
            Choose models from the dropdown above or click "Compare" on any model card in the catalog.
          </p>
          <div className="quick-suggestions-row">
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Quick comparisons:</span>
            <button
              className="quick-compare-btn"
              onClick={() => {
                handleAddModel('qwen-2.5-3b-instruct');
                handleAddModel('llama-3.2-3b-instruct');
              }}
            >
              Qwen 2.5 3B vs Llama 3.2 3B
            </button>
            <button
              className="quick-compare-btn"
              onClick={() => {
                handleAddModel('qwen-2.5-7b-instruct');
                handleAddModel('deepseek-r1-distill-qwen-7b');
              }}
            >
              Qwen 2.5 7B vs DeepSeek R1 7B
            </button>
          </div>
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      {isLoading && (
        <div className="loading-state">
          <span className="spinner" />
          <p>Calculating comparative metrics and benchmark differentials...</p>
        </div>
      )}

      {/* Comparison Matrix Table */}
      {!isLoading && comparison && (
        <div className="comparison-content">
          {/* Summary Verdict Callout */}
          <div className="summary-verdict-card">
            <div className="verdict-header">
              <Sparkles size={16} className="accent-icon" />
              <h3>Evidence-Based Verdict</h3>
            </div>
            <p className="verdict-text">{comparison.summary_verdict}</p>
          </div>

          <div className="comparison-table-wrapper">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th style={{ width: '220px' }}>Metric / Capability</th>
                  {comparison.compared_models.map((m) => (
                    <th key={m.id} className="model-col-header">
                      <div className="model-col-name">{m.name}</div>
                      <div className="model-col-provider">{m.provider}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparison.matrix.map((row, idx) => (
                  <tr key={idx} className={row.category.toLowerCase()}>
                    <td className="metric-cell">
                      <span className="metric-title">{row.metric_name}</span>
                      <span className="metric-cat">{row.category}</span>
                    </td>
                    {comparison.compared_models.map((m) => {
                      const val = row.values[m.id];
                      return (
                        <td key={m.id} className="val-cell">
                          <span className="font-mono">{val !== null && val !== undefined ? String(val) : '—'}</span>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Comparability Disclaimers */}
          {comparison.comparability_notes.length > 0 && (
            <div className="comparability-notes-box">
              <div className="notes-header">
                <AlertCircle size={14} />
                <span>Benchmark Comparability & Data Integrity Notes</span>
              </div>
              <ul>
                {comparison.comparability_notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
