import React from 'react';
import { Cpu, ExternalLink, ShieldCheck, Terminal, Award, Code2 } from 'lucide-react';
import { NavRoute } from '../../types';

interface FooterProps {
  onRouteChange: (route: NavRoute) => void;
}

export const Footer: React.FC<FooterProps> = ({ onRouteChange }) => {
  return (
    <footer className="w-full bg-[#191A18] border-t border-[#41413B] mt-24 py-16 px-4 sm:px-8 lg:px-12 2xl:px-16">
      <div className="w-full flex flex-col gap-12">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand Info */}
          <div className="md:col-span-2 flex flex-col gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-[#242522] border border-[#41413B] flex items-center justify-center text-[#D9823B]">
                <Cpu size={18} />
              </div>
              <span className="text-base font-semibold tracking-tight text-[#F5F0E7]">
                Eval<span className="text-[#D9823B]">Forge</span>20
              </span>
            </div>
            <p className="text-sm text-[#A6A49D] max-w-md leading-relaxed">
              Local-first LLM evaluation platform designed for engineers who demand empirical,
              reproducible, and honest model intelligence without cloud telemetry leaks.
            </p>
            <div className="flex items-center gap-4 text-xs text-[#A6A49D] font-mono">
              <span className="flex items-center gap-1.5 text-[#68B587]">
                <ShieldCheck size={14} /> Zero Data Retention
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 text-[#D9823B]">
                <Terminal size={14} /> Ollama Ready
              </span>
            </div>
          </div>

          {/* Quick Links */}
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#F5F0E7]">
              Platform
            </h4>
            <ul className="flex flex-col gap-2 text-sm text-[#A6A49D]">
              <li>
                <button
                  onClick={() => {
                    onRouteChange('models');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="hover:text-[#F5F0E7] transition-colors cursor-pointer"
                >
                  Model Catalog
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    onRouteChange('compare');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="hover:text-[#F5F0E7] transition-colors cursor-pointer"
                >
                  Model Comparison
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    onRouteChange('evaluate');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="hover:text-[#F5F0E7] transition-colors cursor-pointer"
                >
                  Evaluation Studio
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    onRouteChange('history');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="hover:text-[#F5F0E7] transition-colors cursor-pointer"
                >
                  Run History
                </button>
              </li>
            </ul>
          </div>

          {/* Open Source / Community */}
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#F5F0E7]">
              Repository & Specs
            </h4>
            <ul className="flex flex-col gap-2 text-sm text-[#A6A49D]">
              <li>
                <a
                  href="https://github.com/reddy895/EvalForge20.git"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 hover:text-[#F5F0E7] transition-colors"
                >
                  <Code2 size={14} /> GitHub Repository <ExternalLink size={12} />
                </a>
              </li>
              <li>
                <a
                  href="https://ollama.com"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1.5 hover:text-[#F5F0E7] transition-colors"
                >
                  <Terminal size={14} /> Ollama Library <ExternalLink size={12} />
                </a>
              </li>
              <li>
                <span className="flex items-center gap-1.5 text-xs text-[#78766F]">
                  <Award size={14} /> Local Hardware Benchmarks
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Benchmark Disclaimer Card */}
        <div className="p-4 rounded-2xl bg-[#242522]/60 border border-[#41413B]/80 text-xs text-[#A6A49D] leading-relaxed">
          <strong className="text-[#F5F0E7] font-medium block mb-1">
            Empirical Benchmark Disclaimer:
          </strong>
          All synthetic latency, tokens/sec, and accuracy metrics presented in demo suites are verified
          against standardized validation runs. When running locally with Ollama, actual inference
          throughput will vary according to your system's unified memory bandwidth, GPU compute capability,
          and model quantization level.
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-[#41413B]/60 text-xs text-[#78766F]">
          <p>© {new Date().getFullYear()} EvalForge20. Open source under MIT License.</p>
          <p className="font-mono">Engineered with React 19 • Tailwind CSS • Vite</p>
        </div>
      </div>
    </footer>
  );
};
