import React, { useState } from 'react';
import { SAMPLE_MODELS } from '../../data/models';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { GitCompare, ArrowRight, CheckCircle2, Zap, Cpu, HardDrive } from 'lucide-react';
import { NavRoute } from '../../types';

interface ComparisonPreviewSectionProps {
  onRouteChange: (route: NavRoute) => void;
}

export const ComparisonPreviewSection: React.FC<ComparisonPreviewSectionProps> = ({
  onRouteChange,
}) => {
  const modelA = SAMPLE_MODELS.find((m) => m.id === 'qwen-2.5-7b-instruct') || SAMPLE_MODELS[0];
  const modelB = SAMPLE_MODELS.find((m) => m.id === 'llama-3.1-8b-instruct') || SAMPLE_MODELS[1];

  const [selectedMetric, setSelectedMetric] = useState<'benchmarks' | 'hardware'>('benchmarks');

  return (
    <section id="comparison" className="py-24 px-4 sm:px-6 lg:px-8 2xl:px-12 w-full">
      <div className="w-full max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div className="flex flex-col gap-3">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#D9823B]">
            <GitCompare size={14} />
            <span>SIDE-BY-SIDE BENCHMARKING</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
            Empirical Comparison Matrix
          </h2>
          <p className="text-sm sm:text-base text-[#A6A49D] max-w-xl">
            Compare latency, memory footprints, and task competencies head-to-head before deciding
            which model to embed in production workflows.
          </p>
        </div>

        <Button
          variant="primary"
          onClick={() => onRouteChange('compare')}
          iconRight={<ArrowRight size={14} />}
        >
          Open Comparison Studio
        </Button>
      </div>

      {/* Comparison Preview Table / Card */}
      <div className="rounded-3xl bg-[#242522] border border-[#41413B] shadow-[0_16px_40px_rgba(0,0,0,0.4)] overflow-hidden">
        {/* Toggle Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#41413B] bg-[#191A18]/60">
          <span className="text-xs font-mono text-[#A6A49D]">
            COMPARING: {modelA.name} vs {modelB.name}
          </span>
          <div className="flex rounded-full bg-[#191A18] p-1 border border-[#41413B]">
            <button
              onClick={() => setSelectedMetric('benchmarks')}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                selectedMetric === 'benchmarks'
                  ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                  : 'text-[#A6A49D] hover:text-[#F5F0E7]'
              }`}
            >
              Benchmark Scores
            </button>
            <button
              onClick={() => setSelectedMetric('hardware')}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                selectedMetric === 'hardware'
                  ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                  : 'text-[#A6A49D] hover:text-[#F5F0E7]'
              }`}
            >
              Hardware & Cost
            </button>
          </div>
        </div>

        {/* Models Header Row */}
        <div className="grid grid-cols-3 p-6 border-b border-[#41413B] items-center bg-[#191A18]/30">
          <div className="text-xs font-mono uppercase tracking-wider text-[#A6A49D]">
            Dimension / Metric
          </div>
          <div className="flex flex-col gap-1 pr-4">
            <span className="text-xs text-[#A6A49D]">{modelA.provider}</span>
            <span className="text-base font-bold text-[#F5F0E7]">{modelA.name}</span>
            <Badge variant="installed" size="sm" className="w-fit">
              Ollama Local
            </Badge>
          </div>
          <div className="flex flex-col gap-1 pl-4 border-l border-[#41413B]">
            <span className="text-xs text-[#A6A49D]">{modelB.provider}</span>
            <span className="text-base font-bold text-[#F5F0E7]">{modelB.name}</span>
            <Badge variant="installed" size="sm" className="w-fit">
              Ollama Local
            </Badge>
          </div>
        </div>

        {/* Rows */}
        <div className="divide-y divide-[#41413B]/60 text-sm">
          {/* Row 1: Parameters */}
          <div className="grid grid-cols-3 p-6 items-center hover:bg-white/[0.02] transition-colors">
            <div className="text-xs text-[#A6A49D] flex items-center gap-2">
              <Cpu size={15} className="text-[#D9823B]" /> Parameter Size
            </div>
            <div className="font-mono text-[#F5F0E7] font-semibold">{modelA.parameter_count}</div>
            <div className="font-mono text-[#F5F0E7] font-semibold pl-4 border-l border-[#41413B]">
              {modelB.parameter_count}
            </div>
          </div>

          {/* Row 2: Context Window */}
          <div className="grid grid-cols-3 p-6 items-center hover:bg-white/[0.02] transition-colors">
            <div className="text-xs text-[#A6A49D] flex items-center gap-2">
              <Zap size={15} className="text-[#D9823B]" /> Context Window
            </div>
            <div className="font-mono text-[#F5F0E7]">
              {(modelA.context_window / 1024).toFixed(0)}k tokens
            </div>
            <div className="font-mono text-[#F5F0E7] pl-4 border-l border-[#41413B]">
              {(modelB.context_window / 1024).toFixed(0)}k tokens
            </div>
          </div>

          {selectedMetric === 'benchmarks' ? (
            <>
              {/* Row 3: Coding benchmark */}
              <div className="grid grid-cols-3 p-6 items-center hover:bg-white/[0.02] transition-colors">
                <div className="text-xs text-[#A6A49D] flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-[#68B587]" /> HumanEval (pass@1)
                </div>
                <div className="font-mono text-[#68B587] font-bold text-base">
                  {modelA.benchmarks.find((b) => b.benchmark_name === 'HumanEval')?.score || 84.8}%
                </div>
                <div className="font-mono text-[#F5F0E7] font-bold text-base pl-4 border-l border-[#41413B]">
                  {modelB.benchmarks.find((b) => b.benchmark_name === 'HumanEval')?.score || 72.6}%
                </div>
              </div>

              {/* Row 4: Math & Reasoning */}
              <div className="grid grid-cols-3 p-6 items-center hover:bg-white/[0.02] transition-colors">
                <div className="text-xs text-[#A6A49D] flex items-center gap-2">
                  <CheckCircle2 size={15} className="text-[#68B587]" /> GSM8K (Accuracy)
                </div>
                <div className="font-mono text-[#F5F0E7] font-semibold">
                  {modelA.benchmarks.find((b) => b.benchmark_name === 'GSM8K')?.score || 83.5}%
                </div>
                <div className="font-mono text-[#F5F0E7] font-semibold pl-4 border-l border-[#41413B]">
                  {modelB.benchmarks.find((b) => b.benchmark_name === 'GSM8K')?.score || 84.5}%
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Row 3: Memory Requirements */}
              <div className="grid grid-cols-3 p-6 items-center hover:bg-white/[0.02] transition-colors">
                <div className="text-xs text-[#A6A49D] flex items-center gap-2">
                  <HardDrive size={15} className="text-[#D9823B]" /> Min Required RAM
                </div>
                <div className="font-mono text-[#F5F0E7]">
                  {modelA.hardware.min_ram_gb} GB unified
                </div>
                <div className="font-mono text-[#F5F0E7] pl-4 border-l border-[#41413B]">
                  {modelB.hardware.min_ram_gb} GB unified
                </div>
              </div>

              {/* Row 4: Pricing */}
              <div className="grid grid-cols-3 p-6 items-center hover:bg-white/[0.02] transition-colors">
                <div className="text-xs text-[#A6A49D] flex items-center gap-2">
                  <span className="text-[#D9823B] font-mono">$</span> Pricing / 1M Tokens
                </div>
                <div className="font-mono text-[#68B587] font-bold">$0.00 (Self-Hosted)</div>
                <div className="font-mono text-[#68B587] font-bold pl-4 border-l border-[#41413B]">
                  $0.00 (Self-Hosted)
                </div>
              </div>
            </>
          )}

          {/* Row 5: Tool Calling Support */}
          <div className="grid grid-cols-3 p-6 items-center hover:bg-white/[0.02] transition-colors">
            <div className="text-xs text-[#A6A49D]">Function / Tool Calling</div>
            <div className="text-xs text-[#68B587] flex items-center gap-1.5 font-medium">
              <CheckCircle2 size={14} /> Full Native Support
            </div>
            <div className="text-xs text-[#68B587] flex items-center gap-1.5 font-medium pl-4 border-l border-[#41413B]">
              <CheckCircle2 size={14} /> Full Native Support
            </div>
          </div>
        </div>

        {/* Footer info inside preview */}
        <div className="p-4 bg-[#191A18]/80 border-t border-[#41413B] flex items-center justify-between text-xs text-[#A6A49D]">
          <span>Need to compare 3 or more models simultaneously?</span>
          <button
            onClick={() => onRouteChange('compare')}
            className="text-[#D9823B] hover:underline font-medium cursor-pointer"
          >
            Launch Multi-Model Studio &rarr;
          </button>
        </div>
      </div>
      </div>
    </section>
  );
};
