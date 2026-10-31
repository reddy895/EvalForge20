import React, { useState } from 'react';
import { Terminal, Copy, Check, Shield, Cpu, Lock, Sparkles } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const LocalFirstSection: React.FC = () => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const terminalCommands = [
    {
      title: 'Check Installed Weights',
      cmd: 'ollama list',
      output: `NAME                 ID              SIZE      MODIFIED
qwen2.5:7b           8462280279a0    4.7 GB    2 days ago
llama3.1:8b          46e0c10c039e    4.9 GB    5 days ago
mistral:7b           61e88e884507    4.1 GB    1 week ago`,
    },
    {
      title: 'Run Interactive Test Session',
      cmd: 'ollama run qwen2.5:7b "Write a Python unit test for JWT validation"',
      output: `[Inference Initialized: 4.7GB VRAM Allocated (Q4_K_M)]
>>> Generating tokens at 58.4 tok/s...
import unittest
import jwt
...`,
    },
  ];

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <section id="local-first" className="py-24 px-4 sm:px-6 lg:px-8 2xl:px-12 w-full">
      <div className="w-full max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        {/* Left Column: Copy & Benefits */}
        <div className="lg:col-span-6 flex flex-col gap-6">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#14B8A6]">
            <Terminal size={14} />
            <span>NATIVE OLLAMA INTEGRATION</span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7] leading-tight">
            Run Air-Gapped. <br />
            Evaluate in Complete Privacy.
          </h2>

          <p className="text-sm sm:text-base text-[#A6A49D] leading-relaxed">
            EvalForge20 interfaces natively with local Ollama daemon processes. Test sensitive code,
            proprietary company schema documents, and custom fine-tunes without sending a single byte
            over the external internet.
          </p>

          <div className="flex flex-col gap-4 pt-2">
            <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-[#242522] border border-[#41413B]">
              <div className="w-10 h-10 rounded-xl bg-[#191A18] border border-[#41413B] flex items-center justify-center shrink-0">
                <Shield size={18} className="text-[#68B587]" />
              </div>
              <div className="flex flex-col gap-0.5">
                <h4 className="text-sm font-semibold text-[#F5F0E7]">
                  100% Air-Gapped & Telemetry-Free
                </h4>
                <p className="text-xs text-[#A6A49D] leading-relaxed">
                  Your prompt payloads and evaluation traces never leave localhost. Complete
                  compliance with enterprise data isolation policies.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-[#242522] border border-[#41413B]">
              <div className="w-10 h-10 rounded-xl bg-[#191A18] border border-[#41413B] flex items-center justify-center shrink-0">
                <Cpu size={18} className="text-[#14B8A6]" />
              </div>
              <div className="flex flex-col gap-0.5">
                <h4 className="text-sm font-semibold text-[#F5F0E7]">
                  Hardware-Aware Latency Benchmarking
                </h4>
                <p className="text-xs text-[#A6A49D] leading-relaxed">
                  Direct hardware counters monitor tokens per second, memory allocations, and
                  quantization penalties on your specific CPU / GPU configuration.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 p-4 rounded-2xl bg-[#242522] border border-[#41413B]">
              <div className="w-10 h-10 rounded-xl bg-[#191A18] border border-[#41413B] flex items-center justify-center shrink-0">
                <Lock size={18} className="text-[#F5F0E7]" />
              </div>
              <div className="flex flex-col gap-0.5">
                <h4 className="text-sm font-semibold text-[#F5F0E7]">
                  Zero Cloud Subscriptions Required
                </h4>
                <p className="text-xs text-[#A6A49D] leading-relaxed">
                  Run unlimited test cases, fuzzing iterations, and agent evaluations with zero API
                  metering or surprise monthly bills.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Terminal Window */}
        <div className="lg:col-span-6">
          <div className="rounded-3xl bg-[#191A18] border border-[#41413B] shadow-[0_20px_50px_rgba(0,0,0,0.6)] overflow-hidden">
            {/* Terminal Window Chrome */}
            <div className="flex items-center justify-between px-5 py-3.5 bg-[#242522] border-b border-[#41413B]">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-[#D66D60]/80" />
                <div className="w-3 h-3 rounded-full bg-[#E5914C]/80" />
                <div className="w-3 h-3 rounded-full bg-[#68B587]/80" />
                <span className="ml-2 text-xs font-mono text-[#A6A49D]">bash — ollama@localhost</span>
              </div>
              <Badge variant="outline" size="sm">
                localhost:11434
              </Badge>
            </div>

            {/* Terminal Snippets */}
            <div className="p-6 flex flex-col gap-6 font-mono text-xs">
              {terminalCommands.map((item, idx) => (
                <div key={idx} className="flex flex-col gap-2">
                  <div className="flex items-center justify-between text-[#78766F] text-[11px]">
                    <span># {item.title}</span>
                    <button
                      onClick={() => handleCopy(item.cmd, idx)}
                      className="flex items-center gap-1 text-[#A6A49D] hover:text-[#F5F0E7] transition-colors cursor-pointer"
                    >
                      {copiedIndex === idx ? (
                        <>
                          <Check size={12} className="text-[#68B587]" /> Copied
                        </>
                      ) : (
                        <>
                          <Copy size={12} /> Copy
                        </>
                      )}
                    </button>
                  </div>
                  <div className="flex items-center gap-2 text-[#14B8A6] bg-[#242522] px-3.5 py-2.5 rounded-xl border border-[#41413B]">
                    <span className="text-[#A6A49D]">$</span>
                    <span className="text-[#F5F0E7] font-semibold">{item.cmd}</span>
                  </div>
                  <pre className="text-[#A6A49D] bg-black/30 p-3 rounded-xl border border-[#41413B]/40 leading-relaxed overflow-x-auto whitespace-pre-wrap">
                    {item.output}
                  </pre>
                </div>
              ))}

              <div className="pt-2 border-t border-[#41413B]/60 flex items-center justify-between text-[11px] text-[#78766F]">
                <span className="flex items-center gap-1.5 text-[#68B587]">
                  <Sparkles size={13} /> Ready for local evaluation
                </span>
                <span>Daemon Status: Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </section>
  );
};
