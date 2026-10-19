import React from 'react';
import { Button } from '../ui/Button';
import { HeroComposition } from './HeroComposition';
import { Sparkles, Terminal, ArrowRight, ShieldCheck, Cpu } from 'lucide-react';
import { NavRoute } from '../../types';

interface HeroSectionProps {
  onRouteChange: (route: NavRoute) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onRouteChange }) => {
  return (
    <section className="relative pt-12 pb-20 md:pt-20 md:pb-28 px-4 sm:px-8 lg:px-12 2xl:px-16 w-full overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-12 items-center w-full">
        {/* Left Column: Copy & Actions */}
        <div className="lg:col-span-7 flex flex-col gap-6 text-left">
          {/* Release Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#242522] border border-[#41413B] text-xs text-[#F5F0E7] w-fit shadow-sm">
            <span className="flex h-2 w-2 rounded-full bg-[#D9823B]" />
            <span className="font-mono text-[11px] text-[#A6A49D]">EvalForge20 v2.0</span>
            <span className="text-[#41413B]">|</span>
            <span className="text-[#F5F0E7] font-medium flex items-center gap-1">
              Local-First Model Intelligence <Sparkles size={12} className="text-[#D9823B]" />
            </span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#F5F0E7] leading-[1.12]">
            Find the right model <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#D9823B] via-[#E5914C] to-[#F5F0E7]">
              for every task.
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-lg text-[#A6A49D] max-w-xl leading-relaxed font-normal">
            Local-first LLM evaluation platform designed for production engineers. Benchmark real
            token throughput, function calling accuracy, and memory footprint across local Ollama
            weights and cloud providers with complete privacy.
          </p>

          {/* Dual CTAs */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
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

          {/* Feature Highlights Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-6 border-t border-[#41413B]/70 max-w-xl">
            <div className="flex items-center gap-2 text-xs text-[#A6A49D]">
              <ShieldCheck size={16} className="text-[#68B587] shrink-0" />
              <span>Zero cloud data leaks</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-[#A6A49D]">
              <Cpu size={16} className="text-[#D9823B] shrink-0" />
              <span>VRAM & RAM profiling</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-[#A6A49D] col-span-2 sm:col-span-1">
              <span className="w-2 h-2 rounded-full bg-[#D9823B] shrink-0" />
              <span>Reproducible test suites</span>
            </div>
          </div>
        </div>

        {/* Right Column: Interactive Composition */}
        <div className="lg:col-span-5 w-full">
          <HeroComposition onLaunchStudio={() => onRouteChange('evaluate')} />
        </div>
      </div>
    </section>
  );
};
