import React, { useState, useEffect } from 'react';
import { Server, Cpu, Shield, Save, CheckCircle2 } from 'lucide-react';
import { Button } from '../components/ui/Primitives';

export const SettingsView: React.FC = () => {
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [requestTimeout, setRequestTimeout] = useState('60');
  const [judgeModel, setJudgeModel] = useState('qwen2.5:7b');
  const [enableHardwareMonitoring, setEnableHardwareMonitoring] = useState(true);
  const [sandboxTimeout, setSandboxTimeout] = useState('5');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem(
      'evalforge_settings',
      JSON.stringify({
        ollamaUrl,
        requestTimeout,
        judgeModel,
        enableHardwareMonitoring,
        sandboxTimeout,
      })
    );
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  useEffect(() => {
    const savedSettings = localStorage.getItem('evalforge_settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        if (parsed.ollamaUrl) setOllamaUrl(parsed.ollamaUrl);
        if (parsed.requestTimeout) setRequestTimeout(parsed.requestTimeout);
        if (parsed.judgeModel) setJudgeModel(parsed.judgeModel);
        if (parsed.enableHardwareMonitoring !== undefined)
          setEnableHardwareMonitoring(parsed.enableHardwareMonitoring);
        if (parsed.sandboxTimeout) setSandboxTimeout(parsed.sandboxTimeout);
      } catch {}
    }
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-4">
        <div>
          <h1 className="text-xl font-bold text-[#111827]">Platform Settings</h1>
          <p className="text-xs text-[#64748B] mt-0.5">
            Configure local inference parameters, hardware monitoring, and security sandbox policies
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={handleSave}
          icon={saved ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
        >
          {saved ? 'Saved Successfully' : 'Save Changes'}
        </Button>
      </div>

      <div className="space-y-6">
        {/* OLLAMA LOCAL INFERENCE CONFIG */}
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-[#E2E8F0] pb-3">
            <Server className="w-4 h-4 text-[#2563EB]" />
            <h2 className="text-sm font-bold text-[#111827]">Ollama Local Inference Engine</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-[#111827] mb-1">Ollama Base URL</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                className="w-full px-3 py-2 border border-[#E2E8F0] rounded-md focus:border-[#2563EB] focus:outline-none font-mono text-xs"
              />
              <p className="text-[11px] text-[#64748B] mt-1">Default local daemon address: http://localhost:11434</p>
            </div>

            <div>
              <label className="block font-semibold text-[#111827] mb-1">Inference Timeout (Seconds)</label>
              <input
                type="number"
                value={requestTimeout}
                onChange={(e) => setRequestTimeout(e.target.value)}
                className="w-full px-3 py-2 border border-[#E2E8F0] rounded-md focus:border-[#2563EB] focus:outline-none font-mono text-xs"
              />
              <p className="text-[11px] text-[#64748B] mt-1">Timeout per test-case inference before failing</p>
            </div>

            <div>
              <label className="block font-semibold text-[#111827] mb-1">Default Judge Model</label>
              <input
                type="text"
                value={judgeModel}
                onChange={(e) => setJudgeModel(e.target.value)}
                className="w-full px-3 py-2 border border-[#E2E8F0] rounded-md focus:border-[#2563EB] focus:outline-none font-mono text-xs"
              />
              <p className="text-[11px] text-[#64748B] mt-1">Used for subjective qualitative evaluation tasks</p>
            </div>
          </div>
        </div>

        {/* HARDWARE TELEMETRY & RESOURCES */}
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-[#E2E8F0] pb-3">
            <Cpu className="w-4 h-4 text-[#16A34A]" />
            <h2 className="text-sm font-bold text-[#111827]">Hardware Telemetry & Resource Monitoring</h2>
          </div>

          <div className="text-xs space-y-3">
            <label className="flex items-center gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={enableHardwareMonitoring}
                onChange={(e) => setEnableHardwareMonitoring(e.target.checked)}
                className="rounded border-[#CBD5E1] text-[#2563EB] focus:ring-[#2563EB]"
              />
              <span className="font-semibold text-[#111827]">
                Record CPU, RAM, and GPU/VRAM utilization during evaluation runs
              </span>
            </label>
            <p className="text-[11px] text-[#64748B] pl-6">
              Captures real-time local hardware performance metrics (psutil & PyNVML when available) without fabricating values.
            </p>
          </div>
        </div>

        {/* SECURITY & LOCAL ISOLATION */}
        <div className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2 border-b border-[#E2E8F0] pb-3">
            <Shield className="w-4 h-4 text-[#DC2626]" />
            <h2 className="text-sm font-bold text-[#111827]">Security & Code Execution Sandbox</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-[#111827] mb-1">Code Sandbox Timeout (Seconds)</label>
              <input
                type="number"
                value={sandboxTimeout}
                onChange={(e) => setSandboxTimeout(e.target.value)}
                className="w-full px-3 py-2 border border-[#E2E8F0] rounded-md focus:border-[#2563EB] focus:outline-none font-mono text-xs"
              />
              <p className="text-[11px] text-[#64748B] mt-1">Maximum time allowed for Python code execution tests</p>
            </div>

            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded text-[11px] text-[#64748B] space-y-1">
              <div className="font-semibold text-[#111827]">Local-First Safety Guarantees</div>
              <div>• AST syntax validation & dangerous builtins blocking</div>
              <div>• Strict loop timeout and subprocess isolation</div>
              <div>• Zero external API dependencies & no telemetry phone-home</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
