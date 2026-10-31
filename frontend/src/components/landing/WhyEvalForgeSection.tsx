import React from 'react';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { ShieldCheck, Target, BarChart3, Cpu, Sparkles } from 'lucide-react';

export const WhyEvalForgeSection: React.FC = () => {
  const features = [
    {
      icon: <ShieldCheck size={24} className="text-[#68B587]" />,
      title: 'Zero Data Retention & Local-First',
      description:
        'All prompt inputs, evaluation traces, and test data remain entirely on your local machine. No background telemetry or third-party cloud leaks.',
      metric: '100% Private',
    },
    {
      icon: <Target size={24} className="text-[#14B8A6]" />,
      title: 'Empirical Multi-Turn Assertion',
      description:
        'Move beyond basic perplexity. Test strict JSON schema conformity, code unit tests, and multi-turn function calling with deterministic pass/fail results.',
      metric: 'Deterministic',
    },
    {
      icon: <BarChart3 size={24} className="text-[#14B8A6]" />,
      title: 'Honest Evidence & Real Scores',
      description:
        'Every benchmark is grounded in verifiable test datasets (HumanEval, GSM8K, Schema extraction) with clear distinction between simulated demos and measured runs.',
      metric: 'Verified Data',
    },
    {
      icon: <Cpu size={24} className="text-[#F5F0E7]" />,
      title: 'Unified Hardware & VRAM Profiling',
      description:
        'Know precisely whether a model will fit in 8GB, 16GB, or 32GB of unified memory with quantizations from Q4_K_M to full FP16 before pulling weights.',
      metric: 'VRAM Profiler',
    },
  ];

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 2xl:px-12 w-full bg-[#191A18]/40 border-y border-[#41413B]/40">
      <div className="w-full max-w-7xl mx-auto">
        <div className="flex flex-col items-center text-center max-w-3xl mx-auto mb-16 gap-3">
        <div className="inline-flex items-center gap-2 text-xs font-mono text-[#14B8A6]">
          <Sparkles size={14} />
          <span>ARCHITECTURAL PRINCIPLES</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
          Why Engineers Trust EvalForge20
        </h2>
        <p className="text-sm sm:text-base text-[#A6A49D]">
          Built from the ground up for developers and researchers who require reproducible,
          empirically verified model performance on their own hardware.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feat, idx) => (
          <Card key={idx} hoverable className="p-8">
            <CardHeader className="flex items-center justify-between">
              <div className="w-12 h-12 rounded-2xl bg-[#191A18] border border-[#41413B] flex items-center justify-center">
                {feat.icon}
              </div>
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-[#191A18] border border-[#41413B] text-[#14B8A6]">
                {feat.metric}
              </span>
            </CardHeader>
            <div className="mt-4 flex flex-col gap-2">
              <CardTitle className="text-xl text-[#F5F0E7]">{feat.title}</CardTitle>
              <CardBody className="text-sm text-[#A6A49D] leading-relaxed">
                {feat.description}
              </CardBody>
            </div>
          </Card>
        ))}
      </div>
      </div>
    </section>
  );
};
