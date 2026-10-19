import React from 'react';
import { Layers, Cpu, PlayCircle, FileText, CheckCircle2 } from 'lucide-react';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      number: '01',
      title: 'Select Model & Benchmark Workload',
      desc: 'Pick your active local Ollama weight or remote endpoint. Choose test suites tailored to coding, structured JSON, tool execution, or math.',
      icon: <Layers size={20} className="text-[#D9823B]" />,
    },
    {
      number: '02',
      title: 'Profile Hardware & Context Limits',
      desc: 'Verify whether the model fits comfortably into unified memory or GPU VRAM at chosen context lengths with quantized weights.',
      icon: <Cpu size={20} className="text-[#D9823B]" />,
    },
    {
      number: '03',
      title: 'Execute Deterministic Test Cases',
      desc: 'Evaluate prompts against strict programmatic unit tests, exact matches, and latency timers with full token streaming observability.',
      icon: <PlayCircle size={20} className="text-[#D9823B]" />,
    },
    {
      number: '04',
      title: 'Analyze Trade-offs & Export Audits',
      desc: 'Review side-by-side pass rates, latency distributions, and failure case diffs. Export structured JSON audit logs for CI/CD pipelines.',
      icon: <FileText size={20} className="text-[#D9823B]" />,
    },
  ];

  return (
    <section className="py-20 px-4 sm:px-8 lg:px-12 2xl:px-16 w-full">
      <div className="flex flex-col items-center text-center max-w-2xl mx-auto mb-16 gap-3">
        <div className="inline-flex items-center gap-2 text-xs font-mono text-[#D9823B]">
          <CheckCircle2 size={14} />
          <span>EVALUATION WORKFLOW</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
          How EvalForge20 Works
        </h2>
        <p className="text-sm sm:text-base text-[#A6A49D]">
          A clean, scientific 4-step pipeline designed to give you empirical certainty before
          shipping models to production.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className="p-6 rounded-3xl bg-[#242522] border border-[#41413B] flex flex-col justify-between relative group hover:border-[#D9823B]/60 transition-all hover:-translate-y-1"
          >
            <div>
              <div className="flex items-center justify-between mb-6">
                <span className="text-2xl font-mono font-bold text-[#D9823B]">
                  {step.number}
                </span>
                <div className="w-10 h-10 rounded-full bg-[#191A18] border border-[#41413B] flex items-center justify-center">
                  {step.icon}
                </div>
              </div>
              <h3 className="text-base font-semibold text-[#F5F0E7] mb-2 leading-snug">
                {step.title}
              </h3>
              <p className="text-xs text-[#A6A49D] leading-relaxed">{step.desc}</p>
            </div>
            <div className="mt-6 pt-4 border-t border-[#41413B]/60 flex items-center text-[11px] font-mono text-[#78766F] group-hover:text-[#D9823B] transition-colors">
              <span>Step {step.number} of 04</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
