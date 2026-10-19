import React, { useState, useEffect } from 'react';
import type { OllamaStatus, HardwareProfile } from '../../types';
import { api } from '../../services/api';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

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
    <div className="max-w-4xl mx-auto space-y-10">
      {/* Header */}
      <div className="border-b border-[#393A33] pb-6">
        <h1 className="text-2xl font-bold text-[#F0EEE6] tracking-tight">System & Execution Settings</h1>
        <p className="text-sm text-[#A5A59A] mt-1">
          Configure local Ollama connection, manage local models, and specify hardware specs for tailored recommendations.
        </p>
      </div>

      {/* Ollama Daemon Section */}
      <div className="bg-[#20211E] border border-[#393A33] rounded-lg p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#393A33]">
          <div>
            <h2 className="text-base font-semibold text-[#F0EEE6]">Ollama Inference Daemon</h2>
            <p className="text-xs text-[#A5A59A] mt-0.5">
              Target endpoint: <span className="font-mono text-[#F0EEE6]">{ollamaStatus?.base_url || 'http://localhost:11434'}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={ollamaStatus?.online ? 'success' : 'error'}>
              {ollamaStatus?.online ? 'ONLINE' : 'OFFLINE'}
            </Badge>
            <Button variant="secondary" size="sm" onClick={checkOllama} disabled={checking}>
              {checking ? 'Checking...' : 'Refresh Status'}
            </Button>
          </div>
        </div>

        {/* Offline Guidance */}
        {!ollamaStatus?.online && (
          <div className="bg-[#171816] p-4 rounded border border-amber-900/50 space-y-2">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-xs">
              <span>&#9888;</span> Ollama is currently unreachable at {ollamaStatus?.base_url || 'http://localhost:11434'}
            </div>
            <p className="text-xs text-[#A5A59A]">
              To run live models locally, ensure Ollama is installed and running on your machine:
            </p>
            <pre className="bg-black/50 p-2.5 rounded text-xs font-mono text-[#F0EEE6]">
              ollama serve
            </pre>
            <p className="text-xs text-[#A5A59A]">
              Note: You can still browse the full catalog, view stored evaluations, and run deterministic mock evaluations without a live Ollama daemon.
            </p>
          </div>
        )}

        {/* Installed Models in Ollama */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-3">
            Locally Installed Models ({ollamaStatus?.models.length || 0})
          </h3>
          {ollamaStatus && ollamaStatus.models.length > 0 ? (
            <div className="border border-[#393A33] rounded divide-y divide-[#393A33]">
              {ollamaStatus.models.map((m: any) => (
                <div key={m.name} className="p-3 flex items-center justify-between bg-[#171816]/50">
                  <div>
                    <span className="font-mono text-sm text-[#F0EEE6] font-medium">{m.name}</span>
                    <span className="text-xs text-[#A5A59A] ml-3">
                      {m.size ? `${(m.size / 1024 / 1024 / 1024).toFixed(1)} GB` : ''}
                    </span>
                  </div>
                  <Badge variant="success">Installed</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[#A5A59A] italic">
              {ollamaStatus?.online ? 'No local models found in Ollama repository.' : 'Daemon offline — local models cannot be listed.'}
            </p>
          )}
        </div>

        {/* Explicit Model Pull Form */}
        <div className="pt-4 border-t border-[#393A33] space-y-3">
          <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A]">
            Pull Model Explicitly
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="e.g., llama3.2:1b, qwen2.5:0.5b"
              value={pullModelName}
              onChange={(e) => setPullModelName(e.target.value)}
              disabled={pulling || !ollamaStatus?.online}
              className="flex-1 bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm placeholder-[#A5A59A]/50 focus:outline-none focus:border-[#E58B45]"
            />
            <Button
              variant="primary"
              onClick={handlePullModel}
              disabled={pulling || !pullModelName.trim() || !ollamaStatus?.online}
            >
              {pulling ? 'Pulling Model...' : 'Pull Model'}
            </Button>
          </div>
          <p className="text-[11px] text-[#A5A59A]">
            Explicit pull action triggers Ollama download. Large models (e.g. 70B) may require substantial disk space and network bandwidth.
          </p>
          {pullMessage && (
            <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded text-xs text-emerald-300">
              {pullMessage}
            </div>
          )}
          {pullError && (
            <div className="p-3 bg-red-950/40 border border-red-800/60 rounded text-xs text-red-300">
              {pullError}
            </div>
          )}
        </div>
      </div>

      {/* Hardware Profile Settings */}
      <div className="bg-[#20211E] border border-[#393A33] rounded-lg p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-[#393A33]">
          <div>
            <h2 className="text-base font-semibold text-[#F0EEE6]">Hardware Profile</h2>
            <p className="text-xs text-[#A5A59A] mt-0.5">
              Used by the recommendation engine to calculate RAM/VRAM fit and suggest viable models for your machine.
            </p>
          </div>
          {savedHardwareMsg && (
            <Badge variant="success">Settings Saved</Badge>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-2">
              Operating System
            </label>
            <select
              value={hardware.os}
              onChange={(e) => setHardware({ ...hardware, os: e.target.value })}
              className="w-full bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#E58B45]"
            >
              <option value="Linux">Linux (Ubuntu / Debian / Fedora / Arch)</option>
              <option value="macOS">macOS (Apple Silicon M1/M2/M3/M4)</option>
              <option value="Windows">Windows (WSL2 / Native)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-2">
              System RAM (GB)
            </label>
            <input
              type="number"
              min="4"
              max="512"
              value={hardware.ram_gb}
              onChange={(e) => setHardware({ ...hardware, ram_gb: parseInt(e.target.value) || 16 })}
              className="w-full bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#E58B45]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-2">
              Dedicated GPU VRAM / Unified Memory (GB)
            </label>
            <input
              type="number"
              min="0"
              max="128"
              value={hardware.vram_gb}
              onChange={(e) => setHardware({ ...hardware, vram_gb: parseInt(e.target.value) || 0 })}
              className="w-full bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#E58B45]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[#A5A59A] mb-2">
              GPU Model / Architecture
            </label>
            <input
              type="text"
              value={hardware.gpu_name}
              onChange={(e) => setHardware({ ...hardware, gpu_name: e.target.value })}
              placeholder="e.g. RTX 4090, Apple M3 Pro, CPU only"
              className="w-full bg-[#171816] border border-[#393A33] text-[#F0EEE6] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#E58B45]"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button variant="primary" onClick={handleSaveHardware}>
            Save Hardware Profile
          </Button>
        </div>
      </div>
    </div>
  );
};
