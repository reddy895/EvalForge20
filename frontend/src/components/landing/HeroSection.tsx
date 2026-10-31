import React from 'react';
import { Button } from '../ui/Button';
import { HeroComposition } from './HeroComposition';
import { ArrowRight, BarChart3, Cpu, Play, ShieldCheck, Sparkles, Target, Terminal } from 'lucide-react';
import { NavRoute } from '../../types';

interface HeroSectionProps {
  onRouteChange: (route: NavRoute) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onRouteChange }) => {
  return (
    <section className="relative pt-16 pb-24 md:pt-24 md:pb-32 px-4 sm:px-6 lg:px-8 2xl:px-12 w-full overflow-hidden bg-tech-grid">
      {/* Subtle ambient backdrop radial gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-gradient-to-b from-[#0D9488]/10 via-transparent to-transparent blur-3xl pointer-events-none -z-10" />

      <div className="w-full max-w-7xl mx-auto flex flex-col items-center text-center gap-10">
        {/* Release Pill Badge */}
        <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-[#242522]/90 border border-[#41413B] text-xs text-[#F5F0E7] shadow-sm backdrop-blur-md hover:border-[#0D9488]/60 transition-colors">
          <span className="flex h-2 w-2 rounded-full bg-[#14B8A6] animate-pulse" />
          <span className="font-mono text-[11px] text-[#A6A49D]">EvalForge20 Engine v2.1</span>
          <span className="text-[#41413B]">|</span>
          <span className="text-[#F5F0E7] font-medium flex items-center gap-1.5">
            Evidence-Backed Model Benchmarking <Sparkles size={12} className="text-[#14B8A6]" />
          </span>
        </div>

        {/* Large, Confident Headline */}
        <div className="space-y-4 max-w-4xl">
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-[#F5F0E7] leading-[1.06]">
            Evaluate LLMs & AI Agents with{' '}
            <span className="text-[#14B8A6]">
              Reproducible Evidence
            </span>
          </h1>

          {/* Concise, Clear Value Proposition */}
          <p className="text-base sm:text-xl text-[#A6A49D] max-w-3xl mx-auto leading-relaxed font-normal pt-2">
            Production-grade evaluation engine for deterministic unit assertions, measured token
            throughput, and local Ollama or cloud model profiling with zero data leakage.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Button
            size="lg"
            variant="primary"
            onClick={() => onRouteChange('evaluate')}
            iconLeft={<Play size={16} className="text-[#191A18] fill-[#191A18]" />}
            iconRight={<ArrowRight size={16} />}
          >
            Start Evaluating
          </Button>

          <Button
            size="lg"
            variant="secondary"
            onClick={() => onRouteChange('models')}
            iconLeft={<Terminal size={16} className="text-[#D9823B]" />}
          >
            Explore Model Catalog
          </Button>

          <Button
            size="lg"
            variant="ghost"
            onClick={() => onRouteChange('analytics')}
            iconLeft={<BarChart3 size={16} className="text-[#68B587]" />}
          >
            View Telemetry
          </Button>
        </div>

        {/* Spec Badges Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full max-w-4xl pt-4 text-xs font-mono text-[#A6A49D]">
          <div className="p-3 rounded-2xl bg-[#1F201D]/80 border border-white/5 flex items-center justify-center gap-2 text-center">
            <ShieldCheck size={16} className="text-[#68B587] shrink-0" />
            <span>Zero Cloud Leaks</span>
          </div>
          <div className="p-3 rounded-2xl bg-[#1F201D]/80 border border-white/5 flex items-center justify-center gap-2 text-center">
            <Target size={16} className="text-[#D9823B] shrink-0" />
            <span>Unit Assertions</span>
          </div>
          <div className="p-3 rounded-2xl bg-[#1F201D]/80 border border-white/5 flex items-center justify-center gap-2 text-center">
            <Cpu size={16} className="text-[#68B587] shrink-0" />
            <span>Local Ollama + APIs</span>
          </div>
          <div className="p-3 rounded-2xl bg-[#1F201D]/80 border border-white/5 flex items-center justify-center gap-2 text-center">
            <BarChart3 size={16} className="text-[#D9823B] shrink-0" />
            <span>Evidence-Based 2D Metrics</span>
          </div>
        </div>

        {/* Large Well-Composed Product Preview Workbench */}
        <div className="w-full pt-8">
          <HeroComposition onLaunchStudio={() => onRouteChange('evaluate')} />
        </div>
      </div>
    </section>
  );
};
