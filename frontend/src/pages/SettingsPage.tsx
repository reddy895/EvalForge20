import React, { useEffect, useState } from 'react';
import {
  Settings,
  Database,
  Cpu,
  Layers,
  RefreshCw,
  Key,
  DollarSign,
  Save,
  Eye,
  EyeOff,
  Check,
} from 'lucide-react';
import { api } from '../api/client';
import type { SystemHealthResponse, ReadinessResponse, OllamaDiagnosticReport } from '../api/types';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import './SettingsPage.css';

export const SettingsPage: React.FC = () => {
  const toast = useToast();
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [ollama, setOllama] = useState<OllamaDiagnosticReport | null>(null);
  const [langsmith, setLangsmith] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  // Provider Keys State
  const [openaiKey, setOpenaiKey] = useState<string>(() => localStorage.getItem('evalforge_openai_key') || '');
  const [anthropicKey, setAnthropicKey] = useState<string>(() => localStorage.getItem('evalforge_anthropic_key') || '');
  const [geminiKey, setGeminiKey] = useState<string>(() => localStorage.getItem('evalforge_gemini_key') || '');
  const [nvidiaKey, setNvidiaKey] = useState<string>(() => localStorage.getItem('evalforge_nvidia_key') || '');
  const [showKeys, setShowKeys] = useState<boolean>(false);

  // Hardware Economics State
  const [ollamaEndpoint, setOllamaEndpoint] = useState<string>(
    () => localStorage.getItem('evalforge_ollama_endpoint') || 'http://localhost:11434'
  );
  const [hardwareCostPerHour, setHardwareCostPerHour] = useState<string>(
    () => localStorage.getItem('evalforge_hardware_cost_per_hour') || '0.15'
  );

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
    } catch {
      toast.error('Failed to sync diagnostics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  const handleSaveSettings = () => {
    setIsSaving(true);
    try {
      localStorage.setItem('evalforge_openai_key', openaiKey.trim());
      localStorage.setItem('evalforge_anthropic_key', anthropicKey.trim());
      localStorage.setItem('evalforge_gemini_key', geminiKey.trim());
      localStorage.setItem('evalforge_nvidia_key', nvidiaKey.trim());
      localStorage.setItem('evalforge_ollama_endpoint', ollamaEndpoint.trim());
      localStorage.setItem('evalforge_hardware_cost_per_hour', hardwareCostPerHour.trim());

      toast.success('Configuration and provider credentials saved locally', 'Settings Persisted');
    } catch {
      toast.error('Failed to persist settings in local storage', 'Save Error');
    } finally {
      setTimeout(() => setIsSaving(false), 400);
    }
  };

  return (
    <div className="settings-page">
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Settings & System Configuration</h1>
          <p className="page-header-subtitle">
            Manage provider credentials, local Ollama daemon connection, hardware cost rates, and persistence diagnostics.
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
          <Button
            variant="primary"
            iconLeft={isSaving ? <Check size={13} /> : <Save size={13} />}
            loading={isSaving}
            onClick={handleSaveSettings}
          >
            Save Settings
          </Button>
        </div>
      </div>

      {/* Provider API Credentials */}
      <div className="settings-section-card">
        <div className="settings-section-title">
          <Key size={16} color="var(--accent-primary)" />
          <span>Cloud Provider Credentials</span>
          <button
            type="button"
            className="btn-text"
            style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px', background: 'none', border: 'none', cursor: 'pointer' }}
            onClick={() => setShowKeys(!showKeys)}
          >
            {showKeys ? <EyeOff size={13} /> : <Eye size={13} />}
            {showKeys ? 'Hide Keys' : 'Show Keys'}
          </button>
        </div>
        <p className="settings-section-desc">
          API keys are used for evaluating external cloud models. Local-first evaluations (Ollama & Mock) never require API keys.
        </p>

        <div className="settings-input-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">OpenAI API Key</span>
            <span className="settings-key-desc">For GPT-4o, GPT-4o-mini, and embeddings</span>
          </div>
          <div className="settings-input-control">
            <Input
              type={showKeys ? 'text' : 'password'}
              isMonospace
              placeholder="sk-proj-..."
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
            />
          </div>
        </div>

        <div className="settings-input-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Anthropic API Key</span>
            <span className="settings-key-desc">For Claude 3.5 Sonnet and Haiku</span>
          </div>
          <div className="settings-input-control">
            <Input
              type={showKeys ? 'text' : 'password'}
              isMonospace
              placeholder="sk-ant-..."
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
            />
          </div>
        </div>

        <div className="settings-input-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Google Gemini API Key</span>
            <span className="settings-key-desc">For Gemini 1.5 Pro and Gemini 1.5 Flash</span>
          </div>
          <div className="settings-input-control">
            <Input
              type={showKeys ? 'text' : 'password'}
              isMonospace
              placeholder="AIzaSy..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
            />
          </div>
        </div>

        <div className="settings-input-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">NVIDIA NIM API Key</span>
            <span className="settings-key-desc">For NVIDIA hosted inference and Llama NIM endpoints</span>
          </div>
          <div className="settings-input-control">
            <Input
              type={showKeys ? 'text' : 'password'}
              isMonospace
              placeholder="nvapi-..."
              value={nvidiaKey}
              onChange={(e) => setNvidiaKey(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Local Hardware & Power Economics */}
      <div className="settings-section-card">
        <div className="settings-section-title">
          <DollarSign size={16} color="var(--accent-primary)" />
          <span>Local Hardware Economics & Ollama Endpoint</span>
        </div>
        <p className="settings-section-desc">
          Parameters for estimating local compute, electricity costs, and custom daemon socket endpoints.
        </p>

        <div className="settings-input-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Ollama Base URL</span>
            <span className="settings-key-desc">Local Ollama HTTP socket URL</span>
          </div>
          <div className="settings-input-control">
            <Input
              type="text"
              isMonospace
              placeholder="http://localhost:11434"
              value={ollamaEndpoint}
              onChange={(e) => setOllamaEndpoint(e.target.value)}
            />
          </div>
        </div>

        <div className="settings-input-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Local Hardware Cost Rate ($/hour)</span>
            <span className="settings-key-desc">
              Estimated electricity and machine depreciation rate for local evaluations (Default: $0.15/hr)
            </span>
          </div>
          <div className="settings-input-control">
            <Input
              type="number"
              step="0.01"
              min="0"
              isMonospace
              placeholder="0.15"
              value={hardwareCostPerHour}
              onChange={(e) => setHardwareCostPerHour(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Backend & Engine Diagnostics */}
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
          <span className="font-mono">{health?.version || 'v1.0.0'}</span>
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

      {/* Ollama Local Integration State */}
      <div className="settings-section-card">
        <div className="settings-section-title">
          <Cpu size={16} color="var(--accent-primary)" />
          <span>Ollama Daemon Live Status</span>
        </div>
        <p className="settings-section-desc">
          Live probe response from the local Ollama daemon socket.
        </p>

        <div className="settings-row">
          <div className="settings-label-wrap">
            <span className="settings-key-title">Connection State</span>
            <span className="settings-key-desc">HTTP probe against {ollamaEndpoint}</span>
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

      {/* LangSmith Observability */}
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
