import React, { useState, useEffect } from 'react';
import { Activity, Zap, CheckCircle2, Cpu, HardDrive, ArrowRight } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export const HeroComposition: React.FC<{ onLaunchStudio: () => void }> = ({ onLaunchStudio }) => {
  const [activeTab, setActiveTab] = useState<'metrics' | 'eval'>('metrics');
  const [progress, setProgress] = useState(78);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => (prev >= 100 ? 42 : prev + 2));
    }, 400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="relative w-full max-w-xl mx-auto lg:max-w-none">
      {/* Soft warm glow background (subtle, no harsh neon) */}
      <div className="absolute -inset-1 rounded-3xl bg-gradient-to-r from-[#D9823B]/15 via-transparent to-[#D9823B]/10 blur-xl opacity-70 pointer-events-none" />

      {/* Main Container Card */}
      <div className="relative rounded-3xl bg-[#242522] border border-[#41413B] shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden">
        {/* Top Header of Card */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#41413B] bg-[#191A18]/60">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#68B587] animate-pulse" />
            <span className="text-xs font-mono font-medium text-[#F5F0E7]">
              OLLAMA_LOCAL :: qwen2.5:7b
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" size="sm">
              Q4_K_M
            </Badge>
            <Badge variant="installed" size="sm">
              Live
            </Badge>
          </div>
        </div>

        {/* Inner Content */}
        <div className="p-6 flex flex-col gap-5">
          {/* Subheader & Tab Switcher */}
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs text-[#A6A49D] font-mono">Benchmark Task</span>
              <span className="text-sm font-semibold text-[#F5F0E7]">
                Multi-Turn Tool & Function Calling
              </span>
            </div>
            <div className="flex rounded-full bg-[#191A18] p-1 border border-[#41413B]">
              <button
                onClick={() => setActiveTab('metrics')}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  activeTab === 'metrics'
                    ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                    : 'text-[#A6A49D] hover:text-[#F5F0E7]'
                }`}
              >
                Telemetry
              </button>
              <button
                onClick={() => setActiveTab('eval')}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  activeTab === 'eval'
                    ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                    : 'text-[#A6A49D] hover:text-[#F5F0E7]'
                }`}
              >
                Live Case
              </button>
            </div>
          </div>

          {activeTab === 'metrics' ? (
            /* Telemetry Cards Grid */
            <div className="grid grid-cols-2 gap-3">
              <div className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <Zap size={14} className="text-[#D9823B]" /> Throughput
                  </span>
                  <span className="text-[10px] text-[#68B587] font-mono">+12%</span>
                </div>
                <div className="text-2xl font-bold font-mono text-[#F5F0E7] mt-1">
                  58.4 <span className="text-xs font-normal text-[#A6A49D]">tok/s</span>
                </div>
                <span className="text-[11px] text-[#78766F]">M3 Max Unified Memory</span>
              </div>

              <div className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <Activity size={14} className="text-[#D9823B]" /> TTFT
                  </span>
                  <span className="text-[10px] text-[#A6A49D] font-mono">p95</span>
                </div>
                <div className="text-2xl font-bold font-mono text-[#F5F0E7] mt-1">
                  184 <span className="text-xs font-normal text-[#A6A49D]">ms</span>
                </div>
                <span className="text-[11px] text-[#78766F]">Time to First Token</span>
              </div>

              <div className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <HardDrive size={14} className="text-[#D9823B]" /> VRAM Allocation
                  </span>
                  <span className="text-[10px] text-[#68B587] font-mono">Optimal</span>
                </div>
                <div className="text-2xl font-bold font-mono text-[#F5F0E7] mt-1">
                  5.12 <span className="text-xs font-normal text-[#A6A49D]">GB</span>
                </div>
                <span className="text-[11px] text-[#78766F]">128k Context Window</span>
              </div>

              <div className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
                <div className="flex items-center justify-between text-xs text-[#A6A49D]">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 size={14} className="text-[#68B587]" /> Accuracy
                  </span>
                  <span className="text-[10px] text-[#68B587] font-mono">Verified</span>
                </div>
                <div className="text-2xl font-bold font-mono text-[#F5F0E7] mt-1">
                  94.2 <span className="text-xs font-normal text-[#A6A49D]">%</span>
                </div>
                <span className="text-[11px] text-[#78766F]">24/25 Test Cases Passed</span>
              </div>
            </div>
          ) : (
            /* Live Case Preview */
            <div className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-3 font-mono text-xs">
              <div className="flex items-center justify-between text-[#A6A49D] pb-2 border-b border-[#41413B]">
                <span>Case #03: Schema Validation</span>
                <span className="text-[#68B587]">PASSED (21.4ms)</span>
              </div>
              <div className="text-[#A6A49D]">
                <span className="text-[#D9823B]">$ prompt &gt;</span> Extract user credentials to JSON
                schema: &#123; name, roles, active &#125;
              </div>
              <div className="p-3 rounded-xl bg-[#242522] border border-[#41413B] text-[#F5F0E7]">
                <code>
                  &#123;
                  <br />
                  &nbsp;&nbsp;&quot;name&quot;: &quot;Elena Vance&quot;,
                  <br />
                  &nbsp;&nbsp;&quot;roles&quot;: [&quot;admin&quot;, &quot;analyst&quot;],
                  <br />
                  &nbsp;&nbsp;&quot;active&quot;: true
                  <br />
                  &#125;
                </code>
              </div>
            </div>
          )}

          {/* Test Suite Progress Bar */}
          <div className="flex flex-col gap-1.5 pt-2 border-t border-[#41413B]">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#A6A49D]">Suite Execution Progress</span>
              <span className="font-mono text-[#D9823B] font-medium">{progress}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-[#191A18] overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-[#D9823B] to-[#F5F0E7] transition-all duration-300 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Bottom Action inside card */}
          <div className="flex items-center justify-between pt-1">
            <span className="text-xs text-[#A6A49D] flex items-center gap-1.5">
              <Cpu size={14} className="text-[#D9823B]" /> Zero Cloud Egress
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={onLaunchStudio}
              iconRight={<ArrowRight size={13} />}
            >
              Open Live Runner
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
