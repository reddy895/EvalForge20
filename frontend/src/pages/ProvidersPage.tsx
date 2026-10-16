import React, { useEffect, useState } from 'react';
import { Cpu, Terminal, RefreshCw, Layers, AlertOctagon } from 'lucide-react';
import { api } from '../api/client';
import type { OllamaDiagnosticReport, DetailedModel, ReadinessResponse } from '../api/types';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import './ProvidersPage.css';

export const ProvidersPage: React.FC = () => {
  const [ollamaReport, setOllamaReport] = useState<OllamaDiagnosticReport | null>(null);
  const [ollamaModels, setOllamaModels] = useState<DetailedModel[]>([]);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [langsmithStatus, setLangsmithStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProvidersData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [ollamaRes, readyRes, lsRes] = await Promise.all([
        api.getOllamaStatus().catch((e) => ({
          connected: false,
          base_url: 'http://localhost:11434',
          version: null,
          models_count: 0,
          models: [],
          error_message: e.message || 'Ollama daemon unreachable',
          latency_ms: null,
        })),
        api.getReadiness().catch(() => null),
        api.getLangSmithStatus().catch(() => null),
      ]);

      setOllamaReport(ollamaRes);
      setReadiness(readyRes);
      setLangsmithStatus(lsRes);

      if (ollamaRes.connected) {
        const models = await api.listModels().catch(() => []);
        setOllamaModels(models);
      } else {
        setOllamaModels([]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to inspect provider network status');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProvidersData();
  }, []);

  return (
    <div className="providers-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Models & Providers</h1>
          <p className="page-header-subtitle">
            Local model execution daemons, offline mock drivers, and external telemetry integrations.
          </p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="outline"
            iconLeft={<RefreshCw size={13} />}
            loading={isLoading}
            onClick={fetchProvidersData}
          >
            Probe Connections
          </Button>
        </div>
      </div>

      {error && (
        <div className="toast-item error" role="alert">
          <AlertOctagon size={16} className="toast-icon" />
          <div className="toast-content">
            <div className="toast-title">Provider Discovery Error</div>
            <div className="toast-message">{error}</div>
          </div>
        </div>
      )}

      <div className="providers-grid">
        {/* Ollama Local Provider Card */}
        <div className="provider-detail-card">
          <div className="provider-detail-header">
            <div className="provider-detail-title">
              <Cpu size={16} color="var(--accent-primary)" />
              <span>Ollama Daemon</span>
            </div>
            <Badge variant={ollamaReport?.connected ? 'success' : 'error'} showDot>
              {ollamaReport?.connected ? 'Online (Local)' : 'Offline'}
            </Badge>
          </div>

          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
            Primary local model execution engine running on host machine. Zero external API calls.
          </p>

          <div className="provider-meta-rows">
            <div className="provider-meta-row">
              <span className="text-label">Base URL</span>
              <span className="font-mono">{ollamaReport?.base_url || 'http://localhost:11434'}</span>
            </div>
            <div className="provider-meta-row">
              <span className="text-label">Daemon Version</span>
              <span className="font-mono">{ollamaReport?.version || 'N/A'}</span>
            </div>
            <div className="provider-meta-row">
              <span className="text-label">Probe Latency</span>
              <span className="font-mono">
                {ollamaReport?.latency_ms !== null && ollamaReport?.latency_ms !== undefined
                  ? `${ollamaReport.latency_ms.toFixed(1)} ms`
                  : '—'}
              </span>
            </div>
            <div className="provider-meta-row">
              <span className="text-label">Installed Models</span>
              <span className="font-mono">{ollamaReport?.models_count ?? 0} models</span>
            </div>
          </div>

          {/* Installed Models List */}
          <div className="provider-models-section">
            <span className="text-label">Installed Local Models</span>
            {ollamaModels.length === 0 ? (
              <div
                style={{
                  padding: 'var(--space-md)',
                  background: 'var(--bg-primary)',
                  borderRadius: 'var(--radius-xs)',
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                }}
              >
                {ollamaReport?.connected
                  ? 'No models installed yet. Run "ollama pull qwen2.5:3b" in your shell.'
                  : 'Start Ollama daemon with "ollama serve" to discover local models.'}
              </div>
            ) : (
              ollamaModels.map((m) => (
                <div key={m.name} className="model-pill-item">
                  <span className="model-pill-name">{m.name}</span>
                  <span className="model-pill-meta">
                    {m.details?.parameter_size || 'N/A'} · {(m.size / (1024 * 1024 * 1024)).toFixed(1)} GB
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Deterministic Mock Provider Card */}
        <div className="provider-detail-card">
          <div className="provider-detail-header">
            <div className="provider-detail-title">
              <Terminal size={16} />
              <span>Deterministic Mock Provider</span>
            </div>
            <Badge variant="neutral" showDot>Active Built-in</Badge>
          </div>

          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
            High-throughput offline driver used for regression test verification and platform benchmarks.
          </p>

          <div className="provider-meta-rows">
            <div className="provider-meta-row">
              <span className="text-label">Execution Mode</span>
              <span className="font-mono">In-Memory Async</span>
            </div>
            <div className="provider-meta-row">
              <span className="text-label">Default Model Identifier</span>
              <span className="font-mono">mock-model-v1</span>
            </div>
            <div className="provider-meta-row">
              <span className="text-label">Network Dependency</span>
              <span className="font-mono">None (Offline)</span>
            </div>
            <div className="provider-meta-row">
              <span className="text-label">Readiness Status</span>
              <span className="font-mono" style={{ color: 'var(--status-success)' }}>
                {readiness?.database === 'connected' ? 'Ready' : 'Standby'}
              </span>
            </div>
          </div>

          <div className="provider-models-section">
            <span className="text-label">Mock Model Profiles</span>
            <div className="model-pill-item">
              <span className="model-pill-name">mock-model-v1</span>
              <span className="model-pill-meta">Reference deterministic baseline</span>
            </div>
            <div className="model-pill-item">
              <span className="model-pill-name">mock-agent-v1</span>
              <span className="model-pill-meta">Simulated tool invocation traces</span>
            </div>
          </div>
        </div>

        {/* External Telemetry / LangSmith Optional Integration */}
        <div className="provider-detail-card" style={{ gridColumn: 'span 2' }}>
          <div className="provider-detail-header">
            <div className="provider-detail-title">
              <Layers size={16} />
              <span>External Service Integrations (Optional)</span>
            </div>
            <Badge
              variant={langsmithStatus?.connected ? 'success' : 'neutral'}
              showDot
            >
              {langsmithStatus?.tracing_enabled
                ? langsmithStatus.connected
                  ? 'LangSmith Connected'
                  : 'Configuration Incomplete'
                : 'Disabled (Local-First)'}
            </Badge>
          </div>

          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
            EvalForge20 operates 100% locally by default without requiring third-party cloud accounts. LangSmith tracing can optionally be enabled via environment variables.
          </p>

          <div className="grid-3" style={{ fontSize: '11px', marginTop: 'var(--space-xs)' }}>
            <div className="meta-field">
              <span className="meta-label">Tracing Enabled</span>
              <span className="meta-val">
                {langsmithStatus?.tracing_enabled ? 'True' : 'False (Default)'}
              </span>
            </div>
            <div className="meta-field">
              <span className="meta-label">Endpoint</span>
              <span className="meta-val">
                {langsmithStatus?.endpoint || 'https://api.smith.langchain.com'}
              </span>
            </div>
            <div className="meta-field">
              <span className="meta-label">Project</span>
              <span className="meta-val">
                {langsmithStatus?.project || 'evalforge20-default'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
