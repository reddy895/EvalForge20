import React from 'react';
import { HardDrive, CheckCircle2, Cloud, Sparkles, Scale, PlayCircle, Layers } from 'lucide-react';
import type { ModelSummary } from '../../types';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import './ModelCard.css';

interface ModelCardProps {
  model: ModelSummary;
  onSelect: (modelId: string) => void;
  onCompare: (modelId: string) => void;
  onEvaluate: (modelId: string) => void;
  isComparing?: boolean;
}

export const ModelCard: React.FC<ModelCardProps> = ({
  model,
  onSelect,
  onCompare,
  onEvaluate,
  isComparing = false,
}) => {
  return (
    <div className={`model-card ${model.is_installed ? 'installed' : ''}`}>
      {/* Header */}
      <div className="model-card-header">
        <div>
          <span className="model-provider">{model.provider}</span>
          <h3 className="model-name" onClick={() => onSelect(model.id)} role="button">
            {model.name}
          </h3>
          <span className="model-identifier font-mono">{model.model_identifier}</span>
        </div>

        {/* Installation & Execution Pill */}
        <div>
          {model.is_installed ? (
            <Badge variant="success" title="Downloaded and ready for local inference">
              <CheckCircle2 size={11} style={{ marginRight: '4px' }} />
              Installed
            </Badge>
          ) : model.is_local ? (
            <Badge variant="neutral" title="Runs locally via Ollama">
              <HardDrive size={11} style={{ marginRight: '4px' }} />
              Local
            </Badge>
          ) : (
            <Badge variant="info" title="Hosted Cloud API">
              <Cloud size={11} style={{ marginRight: '4px' }} />
              Cloud API
            </Badge>
          )}
        </div>
      </div>

      {/* Specifications Row */}
      <div className="model-specs-row">
        <div className="spec-item">
          <span className="spec-label">Parameters</span>
          <span className="spec-value font-mono">{model.parameter_count || 'Dense'}</span>
        </div>
        <div className="spec-item">
          <span className="spec-label">Context</span>
          <span className="spec-value font-mono">{(model.context_window / 1024).toFixed(0)}k</span>
        </div>
        <div className="spec-item">
          <span className="spec-label">Min RAM</span>
          <span className="spec-value font-mono">
            {model.hardware_min_ram_gb > 0 ? `${model.hardware_min_ram_gb} GB` : 'API'}
          </span>
        </div>
        <div className="spec-item">
          <span className="spec-label">Cost</span>
          <span className="spec-value">{model.pricing_summary}</span>
        </div>
      </div>

      {/* Verified Headline Benchmark */}
      {model.headline_benchmark_score && (
        <div className="model-benchmark-badge">
          <Sparkles size={12} className="accent-icon" />
          <span className="benchmark-title">{model.headline_benchmark_name}:</span>
          <span className="benchmark-score font-mono font-bold">
            {model.headline_benchmark_score}%
          </span>
        </div>
      )}

      {/* Capabilities & Tasks */}
      <div className="model-tags-row">
        {model.supports_structured_output && (
          <span className="tag-pill">JSON Schema</span>
        )}
        {model.supports_tools && (
          <span className="tag-pill">Tool Calling</span>
        )}
        {model.recommended_tasks.slice(0, 2).map((task) => (
          <span key={task} className="tag-pill task">
            {task.replace('_', ' ')}
          </span>
        ))}
      </div>

      {/* Actions */}
      <div className="model-card-actions">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onSelect(model.id)}
          title="Inspect complete technical profile"
        >
          <Layers size={13} style={{ marginRight: '4px' }} />
          Profile
        </Button>

        <Button
          variant={isComparing ? 'primary' : 'outline'}
          size="sm"
          onClick={() => onCompare(model.id)}
          title="Add to model comparison matrix"
        >
          <Scale size={13} style={{ marginRight: '4px' }} />
          {isComparing ? 'Comparing' : 'Compare'}
        </Button>

        {model.is_local && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onEvaluate(model.model_identifier)}
            title="Run reproducible local evaluation"
          >
            <PlayCircle size={13} style={{ marginRight: '4px' }} />
            Eval
          </Button>
        )}
      </div>
    </div>
  );
};
