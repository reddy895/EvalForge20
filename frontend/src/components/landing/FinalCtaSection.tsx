import React from 'react';
import { Button } from '../ui/Button';
import { Play, ArrowRight, ShieldCheck, Terminal, Cpu } from 'lucide-react';
import { NavRoute } from '../../types';

interface FinalCtaSectionProps {
  onRouteChange: (route: NavRoute) => void;
}

export const FinalCtaSection: React.FC<FinalCtaSectionProps> = ({ onRouteChange }) => {
  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 2xl:px-12 w-full">
      <div className="w-full max-w-7xl mx-auto">
        <div className="relative rounded-3xl bg-gradient-to-b from-[#242522] to-[#191A18] border border-[#41413B] p-10 md:p-16 shadow-[0_24px_64px_rgba(0,0,0,0.6)] overflow-hidden text-center flex flex-col items-center gap-6">
          {/* Soft ember glow behind */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-48 bg-[#D9823B]/10 rounded-full blur-3xl pointer-events-none" />

          {/* Small top badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#191A18] border border-[#41413B] text-xs font-mono text-[#D9823B]">
            <Cpu size={14} />
            <span>ZERO TELEMETRY • LOCAL-FIRST BENCHMARKING</span>
          </div>

          {/* Headline */}
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-[#F5F0E7] max-w-2xl leading-tight">
            Ready to benchmark your models with empirical rigor?
          </h2>

          {/* Subtitle */}
          <p className="text-base text-[#A6A49D] max-w-xl leading-relaxed">
            Start testing local Ollama weights and frontier APIs in seconds. Discover empirical latency,
            context window limits, and function calling accuracy on your own machine.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Button
              size="lg"
              variant="primary"
              onClick={() => onRouteChange('evaluate')}
              iconRight={<Play size={15} className="fill-current" />}
            >
              Launch Evaluation Studio
            </Button>
            <Button
              size="lg"
              variant="secondary"
              onClick={() => onRouteChange('models')}
              iconRight={<ArrowRight size={15} />}
            >
              Explore Full Catalog
            </Button>
          </div>

          {/* Guarantees */}
          <div className="flex flex-wrap items-center justify-center gap-6 pt-6 text-xs text-[#A6A49D]">
            <span className="flex items-center gap-1.5">
              <ShieldCheck size={15} className="text-[#68B587]" /> No API Keys Required for Local
            </span>
            <span className="flex items-center gap-1.5">
              <Terminal size={15} className="text-[#D9823B]" /> Free & Open Source
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#68B587]" /> Instant Interactive Demo
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
