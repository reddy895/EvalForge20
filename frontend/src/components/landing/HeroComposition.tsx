import React, { useState, useEffect } from 'react';
import {
  Activity,
  Zap,
  CheckCircle2,
  Cpu,
  HardDrive,
  ArrowRight,
  Terminal,
  Sparkles,
  Copy,
  Check,
} from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface ModelPreset {
  id: string;
  name: string;
  identifier: string;
  quant: string;
  throughput: number;
  ttft: number;
  vram: number;
  accuracy: number;
  task: string;
  codeSnippet: string;
}

const MODEL_PRESETS: ModelPreset[] = [
  {
    id: 'qwen',
    name: 'Qwen 2.5 7B',
    identifier: 'qwen2.5:7b-instruct-q4_K_M',
    quant: 'Q4_K_M',
    throughput: 58.4,
    ttft: 184,
    vram: 5.12,
    accuracy: 94.2,
    task: 'Multi-Turn Tool & Function Calling',
    codeSnippet: `async def generate_tool_call(query: str):\n    response = await ollama.chat(\n        model="qwen2.5:7b",\n        messages=[{"role": "user", "content": query}],\n        tools=[weather_tool, calendar_tool]\n    )\n    return response["message"]["tool_calls"]`,
  },
  {
    id: 'llama',
    name: 'Llama 3.1 8B',
    identifier: 'llama3.1:8b-instruct-q4_0',
    quant: 'Q4_0',
    throughput: 52.1,
    ttft: 205,
    vram: 5.48,
    accuracy: 91.8,
    task: 'Algorithmic Python Synthesis',
    codeSnippet: `def binary_search_rotated(nums: list[int], target: int) -> int:\n    low, high = 0, len(nums) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if nums[mid] == target: return mid\n        # Verified branch convergence (HumanEval pass@1)\n    return -1`,
  },
  {
    id: 'deepseek',
    name: 'DeepSeek-Coder 6.7B',
    identifier: 'deepseek-coder:6.7b',
    quant: 'Q4_K_M',
    throughput: 64.2,
    ttft: 168,
    vram: 4.85,
    accuracy: 95.6,
    task: 'Constrained JSON Schema Extraction',
    codeSnippet: `{\n  "status": "success",\n  "model": "deepseek-coder:6.7b",\n  "schema_compliance": true,\n  "extracted_entities": ["latency", "throughput", "vram_allocation"],\n  "execution_time_ms": 18.2\n}`,
  },
  {
    id: 'mistral',
    name: 'Mistral 7B v0.3',
    identifier: 'mistral:7b-instruct',
    quant: 'Q4_K_M',
    throughput: 49.8,
    ttft: 218,
    vram: 4.95,
    accuracy: 89.4,
    task: 'Needle-in-a-Haystack Fact Recall',
    codeSnippet: `def verify_context_needle(context: str, key_fact: str) -> bool:\n    # Retrieval precision: 99.4% recall across 32k window\n    return key_fact.lower() in context.lower()`,
  },
];

export const HeroComposition: React.FC<{ onLaunchStudio: () => void }> = ({ onLaunchStudio }) => {
  const [selectedPresetId, setSelectedPresetId] = useState<string>('qwen');
  const [activeTab, setActiveTab] = useState<'metrics' | 'eval'>('metrics');
  const [progress, setProgress] = useState<number>(76);
  const [copied, setCopied] = useState<boolean>(false);

  const activeModel = MODEL_PRESETS.find((m) => m.id === selectedPresetId) || MODEL_PRESETS[0];

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => (prev >= 100 ? 30 : prev + 2));
    }, 350);
    return () => clearInterval(timer);
  }, []);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(activeModel.codeSnippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative w-full max-w-6xl mx-auto">
      {/* Soft warm ambient background glow */}
      <div className="absolute -inset-1.5 rounded-[32px] bg-gradient-to-r from-[#14B8A6]/20 via-[#14B8A6]/10 to-[#14B8A6]/20 blur-2xl opacity-75 pointer-events-none" />

      {/* Main Console Container */}
      <div className="relative rounded-[28px] bg-[#242522] border border-[#41413B] shadow-[0_24px_64px_rgba(0,0,0,0.65)] overflow-hidden">
        {/* Top Mission Control Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 px-6 py-4 border-b border-[#41413B] bg-[#191A18]/85 backdrop-blur-md">
          {/* Preset Model Switcher Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            <span className="text-[11px] font-mono text-[#78766F] uppercase mr-1 flex items-center gap-1">
              <Terminal size={12} className="text-[#14B8A6]" /> Model:
            </span>
            {MODEL_PRESETS.map((preset) => {
              const isActive = preset.id === selectedPresetId;
              return (
                <button
                  key={preset.id}
                  onClick={() => setSelectedPresetId(preset.id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-mono font-medium transition-all cursor-pointer whitespace-nowrap ${
                    isActive
                      ? 'bg-[#242522] text-[#F5F0E7] border border-[#14B8A6] shadow-sm'
                      : 'bg-[#191A18] text-[#A6A49D] hover:text-[#F5F0E7] border border-[#41413B]/70'
                  }`}
                >
                  {preset.name}
                </button>
              );
            })}
          </div>

          {/* Right Status Tags */}
          <div className="flex items-center gap-2 shrink-0">
            <Badge variant="installed" size="sm">
              <span className="w-1.5 h-1.5 rounded-full bg-[#68B587] animate-pulse" />
              Ollama 11434
            </Badge>
            <Badge variant="outline" size="sm">
              {activeModel.quant}
            </Badge>
          </div>
        </div>

        {/* Console Body */}
        <div className="p-6 md:p-8 flex flex-col gap-6">
          {/* Subheader & Mode Toggle */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 border-b border-[#41413B]/70">
            <div className="flex flex-col">
              <span className="text-xs font-mono text-[#14B8A6] flex items-center gap-1.5">
                <Sparkles size={13} /> ACTIVE BENCHMARK WORKLOAD
              </span>
              <h3 className="text-lg font-bold text-[#F5F0E7] mt-0.5">{activeModel.task}</h3>
            </div>

            <div className="flex items-center rounded-full bg-[#191A18] p-1 border border-[#41413B]">
              <button
                onClick={() => setActiveTab('metrics')}
                className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                  activeTab === 'metrics'
                    ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                    : 'text-[#A6A49D] hover:text-[#F5F0E7]'
                }`}
              >
                Hardware HUD
              </button>
              <button
                onClick={() => setActiveTab('eval')}
                className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                  activeTab === 'eval'
                    ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                    : 'text-[#A6A49D] hover:text-[#F5F0E7]'
                }`}
              >
                Execution Trace
              </button>
            </div>
          </div>

          {activeTab === 'metrics' ? (
            /* 4-Card Hardware Telemetry HUD */
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Card 1: Throughput */}
              <div className="p-5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col justify-between hover:border-[#14B8A6]/60 transition-colors">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <Zap size={15} className="text-[#14B8A6]" /> Throughput
                  </span>
                  <span className="text-[10px] text-[#68B587] font-mono">Verified</span>
                </div>
                <div className="my-2">
                  <div className="text-3xl font-extrabold font-mono text-[#F5F0E7] tracking-tight">
                    {activeModel.throughput}{' '}
                    <span className="text-xs font-normal text-[#A6A49D]">tok/s</span>
                  </div>
                </div>
                <span className="text-[11px] text-[#78766F]">Streaming Generation</span>
              </div>

              {/* Card 2: TTFT */}
              <div className="p-5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col justify-between hover:border-[#14B8A6]/60 transition-colors">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <Activity size={15} className="text-[#14B8A6]" /> TTFT (p95)
                  </span>
                  <span className="text-[10px] text-[#A6A49D] font-mono">Native</span>
                </div>
                <div className="my-2">
                  <div className="text-3xl font-extrabold font-mono text-[#F5F0E7] tracking-tight">
                    {activeModel.ttft}{' '}
                    <span className="text-xs font-normal text-[#A6A49D]">ms</span>
                  </div>
                </div>
                <span className="text-[11px] text-[#78766F]">Time to First Token</span>
              </div>

              {/* Card 3: VRAM */}
              <div className="p-5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col justify-between hover:border-[#14B8A6]/60 transition-colors">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <HardDrive size={15} className="text-[#14B8A6]" /> VRAM Weight
                  </span>
                  <span className="text-[10px] text-[#68B587] font-mono">Safe</span>
                </div>
                <div className="my-2">
                  <div className="text-3xl font-extrabold font-mono text-[#F5F0E7] tracking-tight">
                    {activeModel.vram}{' '}
                    <span className="text-xs font-normal text-[#A6A49D]">GB</span>
                  </div>
                </div>
                <span className="text-[11px] text-[#78766F]">Unified RAM allocation</span>
              </div>

              {/* Card 4: Accuracy */}
              <div className="p-5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col justify-between hover:border-[#14B8A6]/60 transition-colors">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 size={15} className="text-[#68B587]" /> Pass Rate
                  </span>
                  <span className="text-[10px] text-[#68B587] font-mono">100% Valid</span>
                </div>
                <div className="my-2">
                  <div className="text-3xl font-extrabold font-mono text-[#68B587] tracking-tight">
                    {activeModel.accuracy}{' '}
                    <span className="text-xs font-normal text-[#A6A49D]">%</span>
                  </div>
                </div>
                <span className="text-[11px] text-[#78766F]">Unit assertions passed</span>
              </div>
            </div>
          ) : (
            /* Execution Trace View */
            <div className="p-5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-3 font-mono text-xs">
              <div className="flex items-center justify-between text-[#A6A49D] pb-2 border-b border-[#41413B]">
                <div className="flex items-center gap-2">
                  <span className="text-[#14B8A6] font-bold">CASE #01</span>
                  <span>{activeModel.identifier}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[#68B587] font-semibold">STATUS: PASSED (19.4ms)</span>
                  <button
                    onClick={handleCopyCode}
                    className="flex items-center gap-1 text-[#A6A49D] hover:text-[#F5F0E7] transition-colors cursor-pointer"
                  >
                    {copied ? <Check size={12} className="text-[#68B587]" /> : <Copy size={12} />}
                    <span>{copied ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#242522] border border-[#41413B] text-[#F5F0E7] overflow-x-auto leading-relaxed">
                <pre>{activeModel.codeSnippet}</pre>
              </div>
            </div>
          )}

          {/* Dynamic Progress Timeline Bar */}
          <div className="flex flex-col gap-2 pt-2 border-t border-[#41413B]/70">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-[#A6A49D] flex items-center gap-1.5">
                <Activity size={13} className="text-[#14B8A6]" /> Continuous Evaluation Stream
              </span>
              <span className="text-[#14B8A6] font-bold">{progress}% Completed</span>
            </div>
            <div className="w-full h-2 rounded-full bg-[#191A18] overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#0D9488] via-[#14B8A6] to-[#F5F0E7] transition-all duration-300 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Bottom Action Footer */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-1">
            <div className="flex items-center gap-3 text-xs text-[#A6A49D] font-mono">
              <span className="flex items-center gap-1.5 text-[#68B587]">
                <Cpu size={14} /> Zero Cloud Egress
              </span>
              <span>•</span>
              <span className="text-[#F5F0E7]">Memory Footprint Checked</span>
            </div>

            <Button
              size="sm"
              variant="primary"
              onClick={onLaunchStudio}
              iconRight={<ArrowRight size={13} />}
            >
              Open Live Runner in Studio
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
