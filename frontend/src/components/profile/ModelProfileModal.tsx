import React from 'react';
import { ModelProfile } from '../../types';
import { Modal } from '../ui/Modal';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import {
  Cpu,
  Zap,
  HardDrive,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  GitCompare,
  Play,
  Calendar,
} from 'lucide-react';

interface ModelProfileModalProps {
  model: ModelProfile | null;
  isOpen: boolean;
  onClose: () => void;
  onCompare: (modelId: string) => void;
  onEvaluate: (modelId: string) => void;
  isCompared: boolean;
}

export const ModelProfileModal: React.FC<ModelProfileModalProps> = ({
  model,
  isOpen,
  onClose,
  onCompare,
  onEvaluate,
  isCompared,
}) => {
  if (!model) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={model.name}
      subtitle={`${model.provider} • ${model.family} Architecture`}
      size="xl"
    >
      <div className="flex flex-col gap-6 max-h-[75vh] overflow-y-auto pr-1">
        {/* Top Badges & Meta */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-2xl bg-[#191A18] border border-[#41413B]">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={model.is_local ? 'installed' : 'outline'} size="md">
              {model.is_local ? 'Ollama Local' : 'Frontier Cloud'}
            </Badge>
            <Badge variant="outline" size="md">
              {model.architecture}
            </Badge>
            <Badge variant="outline" size="md">
              {model.license}
            </Badge>
            {model.is_commercial_use_allowed && (
              <Badge variant="installed" size="md">
                Commercial Use OK
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-[#A6A49D]">
            <Calendar size={13} />
            <span>Released: {model.release_date}</span>
          </div>
        </div>

        {/* Description */}
        <div className="text-sm text-[#F5F0E7] leading-relaxed">
          {model.description}
        </div>

        {/* Key Hardware & Compute Specs Matrix */}
        <div className="flex flex-col gap-3">
          <h4 className="text-xs font-mono uppercase tracking-wider text-[#D9823B]">
            Hardware & Resource Allocation
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono">
            <div className="p-3.5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
              <span className="text-[11px] text-[#A6A49D] flex items-center gap-1.5 font-sans">
                <Cpu size={13} className="text-[#D9823B]" /> Parameters
              </span>
              <span className="text-base font-bold text-[#F5F0E7]">{model.parameter_count}</span>
              <span className="text-[10px] text-[#78766F] font-sans">Quant: {model.quantization || 'FP16'}</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
              <span className="text-[11px] text-[#A6A49D] flex items-center gap-1.5 font-sans">
                <Zap size={13} className="text-[#D9823B]" /> Context Window
              </span>
              <span className="text-base font-bold text-[#F5F0E7]">
                {(model.context_window / 1024).toFixed(0)}k tokens
              </span>
              <span className="text-[10px] text-[#78766F] font-sans">Max sequence length</span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
              <span className="text-[11px] text-[#A6A49D] flex items-center gap-1.5 font-sans">
                <HardDrive size={13} className="text-[#D9823B]" /> Memory Footprint
              </span>
              <span className="text-base font-bold text-[#F5F0E7]">
                {model.hardware.min_ram_gb} GB RAM
              </span>
              <span className="text-[10px] text-[#78766F] font-sans">
                Rec: {model.hardware.recommended_ram_gb} GB
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-1">
              <span className="text-[11px] text-[#A6A49D] flex items-center gap-1.5 font-sans">
                <span className="text-[#68B587] font-mono">$</span> Pricing
              </span>
              <span className="text-base font-bold text-[#68B587]">
                {model.pricing.is_free_local
                  ? 'Free Local'
                  : `$${model.pricing.input_cost_per_m?.toFixed(2)}/1M`}
              </span>
              <span className="text-[10px] text-[#78766F] font-sans">
                {model.pricing.is_free_local ? 'Self-hosted' : 'Cloud API'}
              </span>
            </div>
          </div>
        </div>

        {/* Verified Empirical Benchmarks */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-mono uppercase tracking-wider text-[#D9823B]">
              Verified Benchmark Evidence
            </h4>
            <span className="text-[11px] text-[#68B587] font-mono flex items-center gap-1">
              <ShieldCheck size={13} /> Peer-Reviewed Citations
            </span>
          </div>

          <div className="rounded-2xl border border-[#41413B] bg-[#191A18] overflow-hidden text-xs">
            <div className="grid grid-cols-4 p-3 font-mono font-semibold text-[#A6A49D] border-b border-[#41413B] bg-[#242522]">
              <span>Benchmark</span>
              <span>Metric</span>
              <span>Score</span>
              <span>Evidence Source</span>
            </div>
            <div className="divide-y divide-[#41413B]/60 font-mono">
              {model.benchmarks.map((bm, idx) => (
                <div key={idx} className="grid grid-cols-4 p-3 items-center text-[#F5F0E7]">
                  <span className="font-semibold text-[#D9823B]">{bm.benchmark_name}</span>
                  <span className="text-[#A6A49D]">{bm.metric}</span>
                  <span className="font-bold text-[#68B587] text-sm">{bm.score.toFixed(1)}%</span>
                  <span className="text-[11px] text-[#78766F] truncate">{bm.source}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Strengths & Weaknesses Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#68B587]">
              <CheckCircle2 size={15} /> Validated Strengths
            </div>
            <ul className="flex flex-col gap-1.5 text-xs text-[#A6A49D]">
              {model.strengths.map((str, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-[#68B587] font-mono">•</span>
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="p-4 rounded-2xl bg-[#191A18] border border-[#41413B] flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-[#D66D60]">
              <XCircle size={15} /> Known Limitations
            </div>
            <ul className="flex flex-col gap-1.5 text-xs text-[#A6A49D]">
              {model.weaknesses.map((weak, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-[#D66D60] font-mono">•</span>
                  <span>{weak}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Recommended Tasks */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-mono uppercase tracking-wider text-[#A6A49D]">
            Ideal Workload Match
          </span>
          <div className="flex flex-wrap gap-2">
            {model.recommended_tasks.map((task, i) => (
              <span
                key={i}
                className="px-3 py-1 rounded-full text-xs font-medium bg-[#242522] border border-[#41413B] text-[#F5F0E7]"
              >
                {task}
              </span>
            ))}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-[#41413B] mt-2">
          <Button
            variant={isCompared ? 'primary' : 'outline'}
            onClick={() => onCompare(model.id)}
            iconLeft={<GitCompare size={14} />}
          >
            {isCompared ? 'In Comparison Set' : 'Add to Compare'}
          </Button>

          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                onClose();
                onEvaluate(model.id);
              }}
              iconLeft={<Play size={14} className="fill-current" />}
            >
              Evaluate Model
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
