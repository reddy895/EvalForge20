import React, { useEffect } from 'react';
import type { EvaluatorConfiguration } from '../../api/types';
import './StepEvaluators.css';

interface StepEvaluatorsProps {
  selectedEvaluators: EvaluatorConfiguration[];
  onChange: (evaluators: EvaluatorConfiguration[]) => void;
  onValidChange: (isValid: boolean) => void;
}

interface EvaluatorOption {
  metricId: string;
  name: string;
  category: 'Deterministic' | 'Structural' | 'Model-Based';
  description: string;
}

const AVAILABLE_EVALUATORS: EvaluatorOption[] = [
  {
    metricId: 'exact_match',
    name: 'Exact Match',
    category: 'Deterministic',
    description: 'Strict character-for-character equivalence check against ground truth.',
  },
  {
    metricId: 'normalized_match',
    name: 'Normalized Match',
    category: 'Deterministic',
    description: 'Whitespace, casing, and punctuation-normalized equivalence comparison.',
  },
  {
    metricId: 'token_f1',
    name: 'Token-Level F1 Score',
    category: 'Deterministic',
    description: 'Harmonic mean of token precision and recall across model outputs.',
  },
  {
    metricId: 'json_validity',
    name: 'JSON Validity',
    category: 'Structural',
    description: 'Validates whether model response parses into well-formed JSON syntax.',
  },
  {
    metricId: 'json_schema',
    name: 'JSON Schema Validity',
    category: 'Structural',
    description: 'Enforces strict JSON Schema property and type constraints.',
  },
  {
    metricId: 'response_completeness',
    name: 'Response Completeness',
    category: 'Structural',
    description: 'Verifies length bounds, complete sentences, and structural termination.',
  },
  {
    metricId: 'ollama_judge_answer_relevance',
    name: 'Answer Relevance (Judge)',
    category: 'Model-Based',
    description: 'Evaluates prompt adherence and semantic relevance via local Ollama judge.',
  },
  {
    metricId: 'ollama_judge_factual_correctness',
    name: 'Factual Correctness (Judge)',
    category: 'Model-Based',
    description: 'Verifies factual claims against reference ground truth using local judge.',
  },
  {
    metricId: 'ollama_judge_context_faithfulness',
    name: 'Context Faithfulness (RAG)',
    category: 'Model-Based',
    description: 'Measures groundedness and detects hallucinations against retrieved contexts.',
  },
];

export const StepEvaluators: React.FC<StepEvaluatorsProps> = ({
  selectedEvaluators,
  onChange,
  onValidChange,
}) => {
  useEffect(() => {
    onValidChange(selectedEvaluators.length > 0);
  }, [selectedEvaluators, onValidChange]);

  const isSelected = (metricId: string) =>
    selectedEvaluators.some((e) => e.metric_id === metricId);

  const toggleEvaluator = (opt: EvaluatorOption) => {
    if (isSelected(opt.metricId)) {
      onChange(selectedEvaluators.filter((e) => e.metric_id !== opt.metricId));
    } else {
      onChange([
        ...selectedEvaluators,
        {
          evaluator_name: opt.name,
          metric_id: opt.metricId,
          weight: 1.0,
        },
      ]);
    }
  };

  return (
    <div className="step-evaluators">
      <div className="flex-between">
        <span className="text-label">Available Evaluator Suite</span>
        <span className="font-mono text-label" style={{ color: 'var(--accent-primary)' }}>
          {selectedEvaluators.length} selected
        </span>
      </div>

      <div className="evaluators-grid">
        {AVAILABLE_EVALUATORS.map((opt) => {
          const checked = isSelected(opt.metricId);

          return (
            <div
              key={opt.metricId}
              className={`evaluator-checkbox-item ${checked ? 'selected' : ''}`}
              onClick={() => toggleEvaluator(opt)}
              role="checkbox"
              aria-checked={checked}
              tabIndex={0}
            >
              <input
                type="checkbox"
                className="evaluator-checkbox-input"
                checked={checked}
                onChange={() => {}} // handled by parent container click
                tabIndex={-1}
              />
              <div className="evaluator-info">
                <div className="evaluator-name-row">
                  <span className="evaluator-name">{opt.name}</span>
                  <span className="evaluator-category-pill">{opt.category}</span>
                </div>
                <p className="evaluator-desc">{opt.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
