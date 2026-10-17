import React, { useEffect, useState } from 'react';
import { Cpu, Terminal, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../../api/client';
import type { TargetConfiguration, OllamaDiagnosticReport, DetailedModel } from '../../api/types';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import './StepProvider.css';

interface StepProviderProps {
  target: TargetConfiguration;
  onChange: (target: TargetConfiguration) => void;
  onValidChange: (isValid: boolean) => void;
}

export const StepProvider: React.FC<StepProviderProps> = ({
  target,
  onChange,
  onValidChange,
}) => {
  const [ollamaReport, setOllamaReport] = useState<OllamaDiagnosticReport | null>(null);
  const [ollamaModels, setOllamaModels] = useState<DetailedModel[]>([]);
  const [isChecking, setIsChecking] = useState<boolean>(true);
  const [isManualModelEntry, setIsManualModelEntry] = useState<boolean>(false);

  const checkOllama = async () => {
    setIsChecking(true);
    try {
      const report = await api.getOllamaStatus();
      setOllamaReport(report);
      if (report.connected) {
        const models = await api.listModels().catch(() => []);
        setOllamaModels(models);
      }
    } catch {
      setOllamaReport({
        connected: false,
        base_url: 'http://localhost:11434',
        version: null,
        models_count: 0,
        models: [],
        error_message: 'Failed to communicate with local Ollama daemon',
        latency_ms: null,
      });
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkOllama();
  }, []);

  useEffect(() => {
    const isValid = Boolean(target.target_name.trim() && target.model_identifier.trim());
    onValidChange(isValid);
  }, [target, onValidChange]);

  const selectProviderType = (type: 'ollama' | 'mock' | 'llm') => {
    if (type === 'ollama') {
      const defaultModel =
        ollamaModels.length > 0
          ? ollamaModels[0].name
          : ollamaReport?.models?.[0] || 'qwen2.5:3b';

      onChange({
        ...target,
        target_name: `ollama-${defaultModel.replace(/[^a-zA-Z0-9_-]/g, '_')}`,
        target_type: 'ollama',
        provider_name: 'ollama',
        model_identifier: defaultModel,
        base_url: 'http://localhost:11434',
      });
    } else if (type === 'mock') {
      onChange({
        ...target,
        target_name: 'mock-eval-benchmark',
        target_type: 'mock',
        provider_name: 'mock',
        model_identifier: 'mock-model-v1',
        base_url: null,
      });
    } else {
      onChange({
        ...target,
        target_name: 'custom-llm-target',
        target_type: 'llm',
        provider_name: 'custom',
        model_identifier: 'custom-v1',
      });
    }
  };

  return (
    <div className="step-provider">
      <div className="flex-between" style={{ marginBottom: 'var(--space-md)' }}>
        <span className="text-label">Target Provider</span>
        <Button
          variant="outline"
          size="sm"
          iconLeft={<RefreshCw size={12} />}
          loading={isChecking}
          onClick={checkOllama}
        >
          Check Local Daemons
        </Button>
      </div>

      <div className="provider-cards-grid">
        {/* Ollama Local Provider Card */}
        <div
          className={`provider-card ${target.provider_name === 'ollama' ? 'selected' : ''}`}
          onClick={() => selectProviderType('ollama')}
          role="button"
          tabIndex={0}
        >
          <div className="provider-card-header">
            <div className="flex-row gap-xs">
              <Cpu size={16} color="var(--accent-primary)" />
              <span className="provider-name">Ollama (Local LLM)</span>
            </div>
            {target.provider_name === 'ollama' && (
              <CheckCircle2 size={16} color="var(--accent-primary)" />
            )}
          </div>
          <p className="provider-desc">
            Execute benchmarks against local open weights directly via the Ollama daemon.
          </p>
          <div className="provider-status-line">
            {ollamaReport?.connected ? (
              <>
                <Badge variant="success" showDot>
                  Online ({ollamaReport.version || 'v0.x'})
                </Badge>
                <span>
                  {ollamaReport.models_count} installed
                  {ollamaReport.latency_ms !== null && ollamaReport.latency_ms !== undefined
                    ? ` · ${ollamaReport.latency_ms}ms`
                    : ''}
                </span>
              </>
            ) : (
              <Badge variant="error" showDot>
                Offline (http://localhost:11434)
              </Badge>
            )}
          </div>
        </div>

        {/* Mock Provider Card */}
        <div
          className={`provider-card ${target.provider_name === 'mock' ? 'selected' : ''}`}
          onClick={() => selectProviderType('mock')}
          role="button"
          tabIndex={0}
        >
          <div className="provider-card-header">
            <div className="flex-row gap-xs">
              <Terminal size={16} />
              <span className="provider-name">Deterministic Mock Target</span>
            </div>
            {target.provider_name === 'mock' && (
              <CheckCircle2 size={16} color="var(--accent-primary)" />
            )}
          </div>
          <p className="provider-desc">
            In-memory reference engine for zero-dependency test runs, regression testing, and CI.
          </p>
          <div className="provider-status-line">
            <Badge variant="neutral" showDot>Always Available</Badge>
            <span>Instant execution</span>
          </div>
        </div>
      </div>

      {/* Target Parameters Form */}
      <div className="grid-2">
        <Input
          label="Evaluation Target Name"
          required
          value={target.target_name}
          onChange={(e) => onChange({ ...target, target_name: e.target.value })}
          placeholder="e.g. qwen2.5-3b-benchmark"
        />

        {target.provider_name === 'ollama' && ollamaModels.length > 0 && !isManualModelEntry ? (
          <div className="form-group">
            <div className="flex-between" style={{ marginBottom: '4px' }}>
              <label className="form-label" htmlFor="select-ollama-model">
                <span>Select Installed Model *</span>
              </label>
              <button
                type="button"
                className="btn-text"
                style={{ fontSize: '11px', color: 'var(--accent-primary)', background: 'none', border: 'none', cursor: 'pointer' }}
                onClick={() => setIsManualModelEntry(true)}
              >
                Enter custom identifier manually
              </button>
            </div>
            <select
              id="select-ollama-model"
              className="input-control font-mono"
              value={target.model_identifier}
              onChange={(e) =>
                onChange({
                  ...target,
                  model_identifier: e.target.value,
                  target_name: `ollama-${e.target.value.replace(/[^a-zA-Z0-9_-]/g, '_')}`,
                })
              }
            >
              {ollamaModels.map((m) => (
                <option key={m.name} value={m.name}>
                  {m.name} ({m.details?.parameter_size || 'local'} · {m.details?.quantization_level || 'GGUF'})
                </option>
              ))}
            </select>
            <div className="flex-row gap-xs" style={{ marginTop: '6px', flexWrap: 'wrap' }}>
              {ollamaModels.map((m) => (
                <button
                  key={m.name}
                  type="button"
                  style={{
                    background: target.model_identifier === m.name ? 'var(--accent-subtle)' : 'var(--bg-subtle)',
                    border: target.model_identifier === m.name ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                    color: target.model_identifier === m.name ? 'var(--accent-text)' : 'var(--text-secondary)',
                    borderRadius: 'var(--radius-xs)',
                    padding: '2px 6px',
                    fontSize: '11px',
                    cursor: 'pointer',
                    fontFamily: 'var(--font-mono)',
                  }}
                  onClick={() =>
                    onChange({
                      ...target,
                      model_identifier: m.name,
                      target_name: `ollama-${m.name.replace(/[^a-zA-Z0-9_-]/g, '_')}`,
                    })
                  }
                >
                  {m.name}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="form-group">
            <div className="flex-between" style={{ marginBottom: '4px' }}>
              <label className="form-label" htmlFor="input-model-id">
                <span>Model Identifier *</span>
              </label>
              {target.provider_name === 'ollama' && ollamaModels.length > 0 && (
                <button
                  type="button"
                  className="btn-text"
                  style={{ fontSize: '11px', color: 'var(--accent-primary)', background: 'none', border: 'none', cursor: 'pointer' }}
                  onClick={() => setIsManualModelEntry(false)}
                >
                  Choose from installed models
                </button>
              )}
            </div>
            <Input
              id="input-model-id"
              label=""
              required
              isMonospace
              value={target.model_identifier}
              onChange={(e) => onChange({ ...target, model_identifier: e.target.value })}
              placeholder="e.g. qwen2.5:3b or mock-model-v1"
            />
          </div>
        )}
      </div>

      {target.provider_name === 'ollama' && !ollamaReport?.connected && (
        <div className="toast-item warning" style={{ marginTop: 'var(--space-sm)' }}>
          <AlertCircle size={15} className="toast-icon" />
          <div className="toast-content">
            <div className="toast-title">Ollama Daemon Not Detected</div>
            <div className="toast-message">
              The backend reported that Ollama is unreachable at http://localhost:11434. To enable local inference:
              <ul style={{ margin: '4px 0 0 16px', padding: 0, listStyle: 'disc' }}>
                <li>Start the daemon: <code>ollama serve</code></li>
                <li>Pull a model: <code>ollama pull qwen2.5:3b</code></li>
                <li>Click <strong>Check Local Daemons</strong> above</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Parameters */}
      <div className="grid-3" style={{ marginTop: 'var(--space-md)' }}>
        <Input
          label="Sampling Temperature"
          type="number"
          step="0.1"
          min="0"
          max="2"
          isMonospace
          value={target.temperature}
          onChange={(e) => onChange({ ...target, temperature: parseFloat(e.target.value) || 0 })}
        />
        <Input
          label="Timeout (seconds)"
          type="number"
          min="5"
          max="600"
          isMonospace
          value={target.timeout_seconds}
          onChange={(e) => onChange({ ...target, timeout_seconds: parseFloat(e.target.value) || 60 })}
        />
        <Input
          label="Max Tokens (optional)"
          type="number"
          min="1"
          max="32768"
          isMonospace
          placeholder="Default"
          value={target.max_tokens || ''}
          onChange={(e) =>
            onChange({
              ...target,
              max_tokens: e.target.value ? parseInt(e.target.value, 10) : null,
            })
          }
        />
      </div>
    </div>
  );
};
