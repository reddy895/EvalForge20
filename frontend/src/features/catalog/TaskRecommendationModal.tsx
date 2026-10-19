import React, { useState } from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, HardDrive } from 'lucide-react';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { api } from '../../services/api';
import type { TaskRecommendationResponse } from '../../types';

interface TaskRecommendationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectModel: (modelId: string) => void;
  onEvaluateModel: (modelTag: string) => void;
}

export const TaskRecommendationModal: React.FC<TaskRecommendationModalProps> = ({
  isOpen,
  onClose,
  onSelectModel,
  onEvaluateModel,
}) => {
  const [selectedTask, setSelectedTask] = useState<string>('coding');
  const [preferLocal, setPreferLocal] = useState<boolean>(true);
  const [maxRamGb, setMaxRamGb] = useState<number>(16);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [result, setResult] = useState<TaskRecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tasksList = [
    { id: 'coding', label: 'Code Synthesis & Debugging', desc: 'Synthesizing Python, JavaScript, and complex algorithms' },
    { id: 'reasoning', label: 'Math & Logic Reasoning', desc: 'Multi-step analytical reasoning and mathematical proofs' },
    { id: 'structured_json', label: 'Structured JSON Schema', desc: 'Strict constrained JSON output extraction and validation' },
    { id: 'rag', label: 'RAG & Long Document QA', desc: 'Extended context retrieval with low hallucination' },
    { id: 'agent', label: 'Tool Calling & Agents', desc: 'Multi-turn autonomous function calling' },
  ];

  const handleRunRecommendation = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.getTaskRecommendations(selectedTask, preferLocal, maxRamGb);
      setResult(res);
    } catch (e: any) {
      setError(e.message || 'Failed to generate recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Task-Suitability Recommendation Assistant" maxWidth="720px">
      <div className="recommendation-wizard">
        <p className="wizard-intro">
          Select your target workload and machine capacity. EvalForge20 calculates evidence-based
          model rankings based on verified benchmarks and local memory feasibility.
        </p>

        {/* Task Selection */}
        <div className="form-group">
          <label className="form-label">Target Workload</label>
          <div className="task-options-grid">
            {tasksList.map((t) => (
              <div
                key={t.id}
                className={`task-option-card ${selectedTask === t.id ? 'active' : ''}`}
                onClick={() => setSelectedTask(t.id)}
              >
                <div className="task-card-title">{t.label}</div>
                <div className="task-card-desc">{t.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Constraints */}
        <div className="form-row gap-md" style={{ marginTop: '12px', marginBottom: '16px' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">System RAM Capacity: {maxRamGb} GB</label>
            <input
              type="range"
              min={4}
              max={64}
              step={4}
              value={maxRamGb}
              onChange={(e) => setMaxRamGb(Number(e.target.value))}
              className="range-input"
            />
          </div>

          <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
            <label className="filter-checkbox-label" style={{ marginBottom: '8px' }}>
              <input
                type="checkbox"
                checked={preferLocal}
                onChange={(e) => setPreferLocal(e.target.checked)}
              />
              <span>Prioritize Local Offline Models</span>
            </label>
          </div>
        </div>

        <Button
          variant="primary"
          onClick={handleRunRecommendation}
          loading={isLoading}
          iconLeft={<Sparkles size={15} />}
          style={{ width: '100%', marginBottom: '16px' }}
        >
          Compute Model Recommendations
        </Button>

        {error && <div className="error-banner">{error}</div>}

        {/* Results */}
        {result && (
          <div className="recommendation-results">
            <div className="results-header">
              <span className="results-subtitle">Evaluated Criteria</span>
              <ul className="criteria-list">
                {result.evaluated_criteria.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>

            <div className="recommendation-cards-list">
              {result.recommendations.map((rec, idx) => (
                <div key={rec.model_id} className="rec-card">
                  <div className="rec-card-header">
                    <div>
                      <span className="rec-rank">#{idx + 1}</span>
                      <strong className="rec-name">{rec.model_name}</strong>
                      <span className="rec-provider">({rec.provider})</span>
                    </div>

                    <div className="rec-score-badge">
                      <span className="score-val font-mono font-bold">{rec.match_score}</span>
                      <span className="score-max">/100 match</span>
                    </div>
                  </div>

                  <p className="rec-reason">{rec.recommendation_reason}</p>

                  <div className="rec-details-grid">
                    <div>
                      <span className="rec-detail-label">Evidence & Benchmarks:</span>
                      <ul className="rec-bullets">
                        {rec.key_evidence.map((ev, i) => (
                          <li key={i}>
                            <CheckCircle2 size={12} className="check-icon" />
                            <span>{ev}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <span className="rec-detail-label">Trade-offs & Constraints:</span>
                      <ul className="rec-bullets">
                        {rec.important_tradeoffs.map((to, i) => (
                          <li key={i}>
                            <AlertTriangle size={12} className="warning-icon" />
                            <span>{to}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="rec-card-footer">
                    <Badge variant={rec.is_installed ? 'success' : 'neutral'}>
                      <HardDrive size={11} style={{ marginRight: '4px' }} />
                      {rec.hardware_fit}
                    </Badge>

                    <div className="flex-row gap-xs">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          onClose();
                          onSelectModel(rec.model_id);
                        }}
                      >
                        Profile
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => {
                          onClose();
                          onEvaluateModel(rec.model_name);
                        }}
                      >
                        Evaluate
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
