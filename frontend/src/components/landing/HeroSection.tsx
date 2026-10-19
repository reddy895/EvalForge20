import React from 'react';
import { Button } from '../ui/Button';
import { HeroComposition } from './HeroComposition';
import { Sparkles, Terminal, ArrowRight, ShieldCheck, Cpu, Target } from 'lucide-react';
import { NavRoute } from '../../types';

interface HeroSectionProps {
  onRouteChange: (route: NavRoute) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onRouteChange }) => {
  return (
    <section className="relative pt-12 pb-24 md:pt-20 md:pb-32 px-4 sm:px-8 lg:px-12 2xl:px-16 w-full overflow-hidden bg-tech-grid">
      <div className="flex flex-col items-center text-center max-w-5xl mx-auto gap-8">
        {/* Release Pill Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#242522]/90 border border-[#41413B] text-xs text-[#F5F0E7] shadow-sm backdrop-blur-sm hover:border-[#D9823B]/60 transition-colors">
          <span className="flex h-2 w-2 rounded-full bg-[#D9823B] animate-pulse" />
          <span className="font-mono text-[11px] text-[#A6A49D]">EvalForge20 v2.0</span>
          <span className="text-[#41413B]">|</span>
          <span className="text-[#F5F0E7] font-medium flex items-center gap-1.5">
            Local-First Model Intelligence <Sparkles size={12} className="text-[#D9823B]" />
          </span>
        </div>

        {/* Powerful Main Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-[#F5F0E7] leading-[1.08] max-w-4xl">
          Find the right model <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#D9823B] via-[#E5914C] to-[#F5F0E7]">
            for every task.
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-base sm:text-xl text-[#A6A49D] max-w-2xl leading-relaxed font-normal">
          Local-first LLM evaluation platform designed for production engineers. Benchmark real
          token throughput, function calling accuracy, and memory footprint across local Ollama
          weights and cloud providers with complete privacy.
        </p>

        {/* Dual Centered CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-1">
          <Button
            size="lg"
            variant="primary"
            onClick={() => onRouteChange('models')}
            iconRight={<ArrowRight size={16} />}
          >
            Explore Model Catalog
          </Button>
          <Button
            size="lg"
            variant="secondary"
            onClick={() => onRouteChange('evaluate')}
            iconLeft={<Terminal size={16} className="text-[#D9823B]" />}
          >
            Run Live Benchmark
          </Button>
        </div>

        {/* Centered Spec Badges Row */}
        <div className="flex flex-wrap items-center justify-center gap-6 pt-2 text-xs text-[#A6A49D] font-mono">
          <div className="flex items-center gap-2">
            <ShieldCheck size={16} className="text-[#68B587]" />
            <span>Zero cloud data leaks</span>
          </div>
          <span className="text-[#41413B]">•</span>
          <div className="flex items-center gap-2">
            <Cpu size={16} className="text-[#D9823B]" />
            <span>Hardware VRAM profiling</span>
          </div>
          <span className="text-[#41413B]">•</span>
          <div className="flex items-center gap-2">
            <Target size={16} className="text-[#68B587]" />
            <span>Deterministic unit assertions</span>
          </div>
        </div>

        {/* Centerpiece Interactive Workbench HUD */}
        <div className="w-full pt-8">
          <HeroComposition onLaunchStudio={() => onRouteChange('evaluate')} />
        </div>
      </div>
    </section>
  );
};
