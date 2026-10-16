import React, { useEffect, useState } from 'react';
import { Settings, Database, Cpu, Layers, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import type { SystemHealthResponse, ReadinessResponse, OllamaDiagnosticReport } from '../api/types';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import './SettingsPage.css';

export const SettingsPage: React.FC = () => {
  const toast = useToast();
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [ollama, setOllama] = useState<OllamaDiagnosticReport | null>(null);
  const [langsmith, setLangsmith] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchDiagnostics = async () => {
    setIsLoading(true);
    try {
      const [h, r, o, ls] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getReadiness().catch(() => null),
        api.getOllamaStatus().catch(() => null),
        api.getLangSmithStatus().catch(() => null),
      ]);
      setHealth(h);
      setReadiness(r);
      setOllama(o);
      setLangsmith(ls);
      toast.success('Environment diagnostics synced successfully');
    } catch {
      toast.error('Failed to sync diagnostics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Settings & Diagnostics</h1>
          <p className="page-header-subtitle">
            System configuration, persistence engine diagnostics, and local-first execution parameters.
          </p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="outline"
            iconLeft={<RefreshCw size={13} />}
            loading={isLoading}
            onClick={fetchDiagnostics}
          >
            Refresh Diagnostics
          </Button>
        </div>
      </div>

      {/* Backend & Engine Info */}
      <div className="settings-section-card">
        <div className="settings-section-title">
          <Settings size={16} color="var(--accent-primary)" />
          <span>EvalForge20 Engine Diagnostics</span>
        </div>
        <p className="settings-section-desc">
          Core execution runtime information and active backend configuration.
        </p>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">System Status</span>
            <span className="settings-key-desc">HTTP probe on /health</span>
          </div>
          <Badge variant={health?.status === 'ok' ? 'success' : 'error'} showDot>
            {health?.status === 'ok' ? 'Operational' : 'Unreachable'}
          </Badge>
        </div>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Software Version</span>
            <span className="settings-key-desc">Application semantic version tag</span>
          </div>
          <span className="font-mono">{health?.version || 'v0.1.0'}</span>
        </div>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Environment Mode</span>
            <span className="settings-key-desc">Active configuration environment</span>
          </div>
          <span className="font-mono">{health?.environment || 'development'}</span>
        </div>
      </div>

      {/* Persistence Engine (SQLite) */}
      <div className="settings-section-card">
        <div className="settings-section-title">
          <Database size={16} />
          <span>Persistence Engine (SQLite)</span>
        </div>
        <p className="settings-section-desc">
          Local transactional database storing evaluation runs, test case inputs, and scoring aggregates.
        </p>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Database Connectivity</span>
            <span className="settings-key-desc">Live readiness verification query</span>
          </div>
          <Badge variant={readiness?.database === 'connected' ? 'success' : 'error'} showDot>
            {readiness?.database === 'connected' ? 'Connected' : 'Unavailable'}
          </Badge>
        </div>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Database Location</span>
            <span className="settings-key-desc">SQLite canonical file path</span>
          </div>
          <span className="font-mono">./data/evalforge20.db</span>
        </div>
      </div>

      {/* Ollama Local Integration */}
      <div className="settings-section-card">
        <div className="settings-section-title">
          <Cpu size={16} color="var(--accent-primary)" />
          <span>Ollama Local Daemon</span>
        </div>
        <p className="settings-section-desc">
          Local model execution daemon configuration for offline benchmarking.
        </p>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Daemon Endpoint</span>
            <span className="settings-key-desc">OLLAMA_BASE_URL setting</span>
          </div>
          <span className="font-mono">{ollama?.base_url || 'http://localhost:11434'}</span>
        </div>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Connection State</span>
            <span className="settings-key-desc">HTTP probe against Ollama daemon</span>
          </div>
          <Badge variant={ollama?.connected ? 'success' : 'error'} showDot>
            {ollama?.connected ? `Connected (${ollama.version || 'Active'})` : 'Offline'}
          </Badge>
        </div>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Discovered Local Models</span>
            <span className="settings-key-desc">Models installed on Ollama</span>
          </div>
          <span className="font-mono tabular-nums">{ollama?.models_count ?? 0} models</span>
        </div>
      </div>

      {/* LangSmith Optional Integration */}
      <div className="settings-section-card">
        <div className="settings-section-title">
          <Layers size={16} />
          <span>LangSmith Observability (Optional)</span>
        </div>
        <p className="settings-section-desc">
          Third-party tracing integration. Operates 100% disabled by default to preserve local-first privacy.
        </p>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Tracing Enabled</span>
            <span className="settings-key-desc">Configured via LANGSMITH_TRACING</span>
          </div>
          <Badge variant={langsmith?.tracing_enabled ? 'accent' : 'neutral'}>
            {langsmith?.tracing_enabled ? 'Enabled' : 'Disabled (Default)'}
          </Badge>
        </div>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">API Endpoint</span>
            <span className="settings-key-desc">Target LangSmith ingest endpoint</span>
          </div>
          <span className="font-mono">{langsmith?.endpoint || 'https://api.smith.langchain.com'}</span>
        </div>
      </div>
    </div>
  );
};
