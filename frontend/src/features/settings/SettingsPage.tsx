import React, { useState, useEffect } from 'react';
import type { OllamaStatus, HardwareProfile } from '../../types';
import { api } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import './SettingsPage.css';

export const SettingsPage: React.FC = () => {
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);
  const [checking, setChecking] = useState(false);
  const [pullModelName, setPullModelName] = useState('');
  const [pulling, setPulling] = useState(false);
  const [pullMessage, setPullMessage] = useState<string | null>(null);
  const [pullError, setPullError] = useState<string | null>(null);

  // Hardware profile state
  const [hardware, setHardware] = useState<HardwareProfile>({
    os: 'Linux',
    ram_gb: 32,
    vram_gb: 12,
    gpu_name: 'NVIDIA RTX / Unified Memory',
    cpu_cores: 12,
    disk_available_gb: 100,
  });
  const [savedHardwareMsg, setSavedHardwareMsg] = useState(false);

  const checkOllama = async () => {
    try {
      setChecking(true);
      const status = await api.getOllamaStatus();
      setOllamaStatus(status);
    } catch (err: any) {
      setOllamaStatus({
        online: false,
        models: [],
        base_url: 'http://localhost:11434',
        error: err.message,
      });
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkOllama();
    // Load local hardware settings if present
    const saved = localStorage.getItem('evalforge20_hardware_profile');
    if (saved) {
      try {
        setHardware(JSON.parse(saved));
      } catch {
        // ignore
      }
    }
  }, []);

  const handlePullModel = async () => {
    if (!pullModelName.trim()) return;
    try {
      setPulling(true);
      setPullMessage(null);
      setPullError(null);
      const result = await api.pullOllamaModel(pullModelName.trim());
      setPullMessage(result.message);
      setPullModelName('');
      await checkOllama();
    } catch (err: any) {
      setPullError(err.message || 'Failed to pull model via Ollama.');
    } finally {
      setPulling(false);
    }
  };

  const handleSaveHardware = () => {
    localStorage.setItem('evalforge20_hardware_profile', JSON.stringify(hardware));
    setSavedHardwareMsg(true);
    setTimeout(() => setSavedHardwareMsg(false), 3000);
  };

  return (
    <div className="page-container settings-page-container">
      {/* Header */}
      <div className="settings-header-bar">
        <h1 className="settings-header-title">System & Execution Settings</h1>
        <p className="settings-header-subtitle">
          Configure local Ollama connection, manage local models, and specify hardware specs for tailored recommendations.
        </p>
      </div>

      {/* Ollama Daemon Section */}
      <div className="settings-card">
        <div className="settings-card-header">
          <div className="card-title-group">
            <h2>Ollama Inference Daemon</h2>
            <p className="card-endpoint-text">
              Target endpoint: <span className="font-mono">{ollamaStatus?.base_url || 'http://localhost:11434'}</span>
            </p>
          </div>
          <div className="flex-row gap-xs">
            <Badge variant={ollamaStatus?.online ? 'success' : 'error'}>
              {ollamaStatus?.online ? 'ONLINE' : 'OFFLINE'}
            </Badge>
            <Button variant="outline" size="sm" onClick={checkOllama} disabled={checking}>
              {checking ? 'Checking...' : 'Refresh Status'}
            </Button>
          </div>
        </div>

        {/* Offline Guidance */}
        {!ollamaStatus?.online && (
          <div className="offline-warning-banner">
            <div className="warning-banner-title">
              <span>&#9888;</span> Ollama is currently unreachable at {ollamaStatus?.base_url || 'http://localhost:11434'}
            </div>
            <p className="warning-banner-text">
              To run live models locally, ensure Ollama is installed and running on your machine:
            </p>
            <div className="terminal-command-box">
              ollama serve
            </div>
            <p className="warning-banner-text" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Note: You can still browse the full catalog, view stored evaluations, and run deterministic mock evaluations without a live Ollama daemon.
            </p>
          </div>
        )}

        {/* Installed Models in Ollama */}
        <div className="installed-models-section">
          <label className="field-label">
            Locally Installed Models ({ollamaStatus?.models.length || 0})
          </label>
          {ollamaStatus && ollamaStatus.models.length > 0 ? (
            <div className="installed-models-list">
              {ollamaStatus.models.map((m: any) => (
                <div key={m.name} className="installed-model-item">
                  <div>
                    <span className="model-item-name font-mono">{m.name}</span>
                    <span className="model-item-size font-mono">
                      {m.size ? `${(m.size / 1024 / 1024 / 1024).toFixed(1)} GB` : ''}
                    </span>
                  </div>
                  <Badge variant="success">Installed</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="field-helper" style={{ fontStyle: 'italic' }}>
              {ollamaStatus?.online
                ? 'No local models found in Ollama repository.'
                : 'Daemon offline — local models cannot be listed.'}
            </p>
          )}
        </div>

        {/* Explicit Model Pull Form */}
        <div className="model-pull-box">
          <label className="field-label">
            Pull Model Explicitly
          </label>
          <div className="pull-input-row">
            <input
              type="text"
              placeholder="e.g. llama3.2:1b, qwen2.5:0.5b"
              value={pullModelName}
              onChange={(e) => setPullModelName(e.target.value)}
              disabled={pulling || !ollamaStatus?.online}
              className="pull-input"
            />
            <Button
              variant="primary"
              onClick={handlePullModel}
              disabled={pulling || !pullModelName.trim() || !ollamaStatus?.online}
              loading={pulling}
            >
              {pulling ? 'Pulling Model...' : 'Pull Model'}
            </Button>
          </div>
          <p className="field-helper">
            Explicit pull action triggers Ollama download. Large models (e.g. 70B) may require substantial disk space and network bandwidth.
          </p>
          {pullMessage && (
            <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded text-xs text-emerald-300">
              {pullMessage}
            </div>
          )}
          {pullError && (
            <div className="error-banner">
              {pullError}
            </div>
          )}
        </div>
      </div>

      {/* Hardware Profile Settings */}
      <div className="settings-card">
        <div className="settings-card-header">
          <div className="card-title-group">
            <h2>Hardware Profile</h2>
            <p className="card-endpoint-text">
              Used by the recommendation engine to calculate RAM/VRAM fit and suggest viable models for your machine.
            </p>
          </div>
          {savedHardwareMsg && (
            <Badge variant="success">Settings Saved</Badge>
          )}
        </div>

        <div className="hardware-form-grid">
          <div className="config-field">
            <label className="field-label">Operating System</label>
            <select
              value={hardware.os}
              onChange={(e) => setHardware({ ...hardware, os: e.target.value })}
              className="field-select"
            >
              <option value="Linux">Linux (Ubuntu / Debian / Fedora / Arch)</option>
              <option value="macOS">macOS (Apple Silicon M1/M2/M3/M4)</option>
              <option value="Windows">Windows (WSL2 / Native)</option>
            </select>
          </div>

          <div className="config-field">
            <label className="field-label">System RAM (GB)</label>
            <input
              type="number"
              min="4"
              max="512"
              value={hardware.ram_gb}
              onChange={(e) => setHardware({ ...hardware, ram_gb: parseInt(e.target.value) || 16 })}
              className="field-input font-mono"
            />
          </div>

          <div className="config-field">
            <label className="field-label">Dedicated GPU VRAM / Unified Memory (GB)</label>
            <input
              type="number"
              min="0"
              max="128"
              value={hardware.vram_gb}
              onChange={(e) => setHardware({ ...hardware, vram_gb: parseInt(e.target.value) || 0 })}
              className="field-input font-mono"
            />
          </div>

          <div className="config-field">
            <label className="field-label">GPU Model / Architecture</label>
            <input
              type="text"
              value={hardware.gpu_name}
              onChange={(e) => setHardware({ ...hardware, gpu_name: e.target.value })}
              placeholder="e.g. RTX 4090, Apple M3 Pro, CPU only"
              className="field-input"
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '8px' }}>
          <Button variant="primary" onClick={handleSaveHardware}>
            Save Hardware Profile
          </Button>
        </div>
      </div>
    </div>
  );
};
