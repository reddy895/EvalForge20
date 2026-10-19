import React, { useState } from 'react';
import { SAMPLE_MODELS } from '../../data/models';
import { NavRoute } from '../../types';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  GitCompare,
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
  Cpu,
  Zap,
  HardDrive,
  Award,
  Play,
  RotateCcw,
} from 'lucide-react';

interface ComparePageProps {
  compareModelIds: string[];
  onToggleCompare: (modelId: string) => void;
  onClearCompare: () => void;
  onRouteChange: (route: NavRoute) => void;
  onSelectModelForEvaluation: (modelId: string) => void;
}

export const ComparePage: React.FC<ComparePageProps> = ({
  compareModelIds,
  onToggleCompare,
  onClearCompare,
  onRouteChange,
  onSelectModelForEvaluation,
}) => {
  const [selectedDropdownModelId, setSelectedDropdownModelId] = useState<string>('');

  // Default to 2 top models if none selected
  const activeIds =
    compareModelIds.length > 0
      ? compareModelIds
      : ['qwen-2.5-7b-instruct', 'llama-3.1-8b-instruct'];

  const modelsToCompare = SAMPLE_MODELS.filter((m) => activeIds.includes(m.id));

  const availableToAdd = SAMPLE_MODELS.filter((m) => !activeIds.includes(m.id));

  const handleAddSelected = () => {
    if (selectedDropdownModelId) {
      onToggleCompare(selectedDropdownModelId);
      setSelectedDropdownModelId('');
    }
  };

  // Find all distinct benchmark names across compared models
  const allBenchmarks = Array.from(
    new Set(modelsToCompare.flatMap((m) => m.benchmarks.map((b) => b.benchmark_name)))
  );

  return (
    <div className="py-10 px-4 sm:px-8 lg:px-12 2xl:px-16 w-full flex flex-col gap-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#41413B]">
        <div className="flex flex-col gap-2">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#D9823B]">
            <GitCompare size={14} />
            <span>SIDE-BY-SIDE EVALUATION STUDIO</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
            Model Comparison
          </h1>
          <p className="text-sm text-[#A6A49D] max-w-xl">
            Analyze architectural parameters, token throughput trade-offs, and empirical benchmark
            results across multiple candidate models concurrently.
          </p>
        </div>

        {/* Top Actions */}
        <div className="flex flex-wrap items-center gap-3">
          {availableToAdd.length > 0 && activeIds.length < 4 && (
            <div className="flex items-center gap-2 bg-[#242522] p-1.5 rounded-full border border-[#41413B]">
              <select
                value={selectedDropdownModelId}
                onChange={(e) => setSelectedDropdownModelId(e.target.value)}
                className="bg-transparent text-xs text-[#F5F0E7] px-3 py-1 outline-none font-medium cursor-pointer"
              >
                <option value="" disabled className="bg-[#191A18] text-[#78766F]">
                  Add model to compare...
                </option>
                {availableToAdd.map((m) => (
                  <option key={m.id} value={m.id} className="bg-[#191A18] text-[#F5F0E7]">
                    {m.name} ({m.provider})
                  </option>
                ))}
              </select>
              <Button
                size="sm"
                variant="primary"
                onClick={handleAddSelected}
                disabled={!selectedDropdownModelId}
                iconLeft={<Plus size={13} />}
              >
                Add
              </Button>
            </div>
          )}

          {activeIds.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onClearCompare}
              iconLeft={<RotateCcw size={13} />}
            >
              Reset Comparison
            </Button>
          )}
        </div>
      </div>

      {/* Comparison Grid Matrix */}
      {modelsToCompare.length === 0 ? (
        <div className="py-20 px-6 rounded-3xl bg-[#242522] border border-[#41413B] text-center flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#191A18] border border-[#41413B] flex items-center justify-center text-[#D9823B]">
            <GitCompare size={20} />
          </div>
          <h3 className="text-lg font-semibold text-[#F5F0E7]">No models in comparison set</h3>
          <p className="text-sm text-[#A6A49D] max-w-sm">
            Select at least two models from the catalog to inspect their specifications, memory
            requirements, and empirical benchmarks.
          </p>
          <Button variant="primary" size="sm" onClick={() => onRouteChange('models')}>
            Browse Model Catalog
          </Button>
        </div>
      ) : (
        <div className="rounded-3xl bg-[#242522] border border-[#41413B] overflow-hidden shadow-[0_16px_40px_rgba(0,0,0,0.4)]">
          {/* Header Row: Model Cards */}
          <div
            className="grid border-b border-[#41413B] bg-[#191A18]/60"
            style={{
              gridTemplateColumns: `220px repeat(${modelsToCompare.length}, minmax(220px, 1fr))`,
            }}
          >
            <div className="p-6 flex flex-col justify-end text-xs font-mono uppercase tracking-wider text-[#A6A49D] border-r border-[#41413B]">
              Models ({modelsToCompare.length}/4)
            </div>

            {modelsToCompare.map((model) => (
              <div
                key={model.id}
                className="p-6 flex flex-col justify-between gap-4 border-r border-[#41413B] last:border-r-0"
              >
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono text-[#A6A49D]">{model.provider}</span>
                    <button
                      onClick={() => onToggleCompare(model.id)}
                      className="text-[#A6A49D] hover:text-[#D66D60] p-1 transition-colors cursor-pointer"
                      title="Remove from comparison"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  <h3 className="text-lg font-bold text-[#F5F0E7] leading-snug">{model.name}</h3>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    <Badge variant={model.is_local ? 'installed' : 'outline'} size="sm">
                      {model.is_local ? 'Ollama' : 'Cloud'}
                    </Badge>
                    <Badge variant="outline" size="sm">
                      {model.parameter_count}
                    </Badge>
                  </div>
                </div>

                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => onSelectModelForEvaluation(model.id)}
                  iconLeft={<Play size={12} className="fill-current" />}
                  className="w-full justify-center"
                >
                  Evaluate
                </Button>
              </div>
            ))}
          </div>

          {/* Section 1: Hardware & Compute Specifications */}
          <div className="p-4 bg-[#191A18]/40 border-b border-[#41413B] text-xs font-mono font-bold text-[#D9823B] uppercase tracking-wider">
            Compute & Hardware Constraints
          </div>

          <div
            className="grid divide-y divide-[#41413B]/60 text-xs"
            style={{
              gridTemplateColumns: `220px repeat(${modelsToCompare.length}, minmax(220px, 1fr))`,
            }}
          >
            {/* Architecture */}
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B] flex items-center gap-1.5">
              <Cpu size={14} className="text-[#D9823B]" /> Architecture
            </div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 text-[#F5F0E7] font-mono border-r border-[#41413B] last:border-r-0">
                {m.architecture}
              </div>
            ))}

            {/* Context Window */}
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B] flex items-center gap-1.5">
              <Zap size={14} className="text-[#D9823B]" /> Context Window
            </div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 font-mono font-bold text-[#F5F0E7] border-r border-[#41413B] last:border-r-0">
                {(m.context_window / 1024).toFixed(0)}k tokens
              </div>
            ))}

            {/* RAM Requirements */}
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B] flex items-center gap-1.5">
              <HardDrive size={14} className="text-[#D9823B]" /> Min Required RAM
            </div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 font-mono text-[#F5F0E7] border-r border-[#41413B] last:border-r-0">
                {m.hardware.min_ram_gb} GB unified
              </div>
            ))}

            {/* Pricing */}
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B]">Pricing / Unit</div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 font-mono text-[#68B587] font-semibold border-r border-[#41413B] last:border-r-0">
                {m.pricing.is_free_local ? 'Free Local (Ollama)' : `$${m.pricing.input_cost_per_m?.toFixed(2)}/1M`}
              </div>
            ))}

            {/* License */}
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B]">License</div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 text-[#A6A49D] border-r border-[#41413B] last:border-r-0">
                {m.license}
              </div>
            ))}
          </div>

          {/* Section 2: Verified Empirical Benchmarks */}
          <div className="p-4 bg-[#191A18]/40 border-y border-[#41413B] text-xs font-mono font-bold text-[#D9823B] uppercase tracking-wider flex items-center justify-between">
            <span>Verified Benchmark Scores</span>
            <span className="text-[11px] text-[#A6A49D] font-normal normal-case">
              Scores highlighted in green represent leading measurements
            </span>
          </div>

          <div
            className="grid divide-y divide-[#41413B]/60 text-xs"
            style={{
              gridTemplateColumns: `220px repeat(${modelsToCompare.length}, minmax(220px, 1fr))`,
            }}
          >
            {allBenchmarks.map((bmName) => {
              // Find max score among compared models
              const scores = modelsToCompare.map((m) => {
                const bm = m.benchmarks.find((b) => b.benchmark_name === bmName);
                return bm ? bm.score : 0;
              });
              const maxScore = Math.max(...scores);

              return (
                <React.Fragment key={bmName}>
                  <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B] flex items-center gap-1.5 font-medium">
                    <Award size={14} className="text-[#D9823B]" /> {bmName}
                  </div>
                  {modelsToCompare.map((m) => {
                    const bm = m.benchmarks.find((b) => b.benchmark_name === bmName);
                    const isWinner = bm && bm.score === maxScore && maxScore > 0;

                    return (
                      <div
                        key={m.id}
                        className="p-4 font-mono border-r border-[#41413B] last:border-r-0 flex items-center justify-between"
                      >
                        {bm ? (
                          <>
                            <span
                              className={`text-sm font-bold ${
                                isWinner ? 'text-[#68B587]' : 'text-[#F5F0E7]'
                              }`}
                            >
                              {bm.score.toFixed(1)}%
                            </span>
                            <span className="text-[10px] text-[#78766F]">{bm.metric}</span>
                          </>
                        ) : (
                          <span className="text-[#78766F] italic">Not reported</span>
                        )}
                      </div>
                    );
                  })}
                </React.Fragment>
              );
            })}

            {/* Tool Calling Support */}
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B]">
              Tool / Function Calling
            </div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 border-r border-[#41413B] last:border-r-0 flex items-center gap-1.5">
                {m.supports_tools ? (
                  <span className="text-[#68B587] flex items-center gap-1 font-medium">
                    <CheckCircle2 size={14} /> Full Native
                  </span>
                ) : (
                  <span className="text-[#A6A49D] flex items-center gap-1">
                    <XCircle size={14} /> Prompt Emulation
                  </span>
                )}
              </div>
            ))}

            {/* JSON Schema Support */}
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B]">
              Structured JSON Schema
            </div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 border-r border-[#41413B] last:border-r-0 flex items-center gap-1.5">
                {m.supports_structured_output ? (
                  <span className="text-[#68B587] flex items-center gap-1 font-medium">
                    <CheckCircle2 size={14} /> Constrained Grammar
                  </span>
                ) : (
                  <span className="text-[#A6A49D] flex items-center gap-1">
                    <XCircle size={14} /> Basic JSON
                  </span>
                )}
              </div>
            ))}
          </div>

          {/* Section 3: Ideal Tasks */}
          <div className="p-4 bg-[#191A18]/40 border-y border-[#41413B] text-xs font-mono font-bold text-[#D9823B] uppercase tracking-wider">
            Recommended Workload Profiles
          </div>

          <div
            className="grid text-xs"
            style={{
              gridTemplateColumns: `220px repeat(${modelsToCompare.length}, minmax(220px, 1fr))`,
            }}
          >
            <div className="p-4 text-[#A6A49D] font-mono border-r border-[#41413B]">
              Recommended Tasks
            </div>
            {modelsToCompare.map((m) => (
              <div key={m.id} className="p-4 border-r border-[#41413B] last:border-r-0 flex flex-wrap gap-1.5">
                {m.recommended_tasks.map((task, i) => (
                  <span
                    key={i}
                    className="px-2.5 py-1 rounded-full text-[11px] bg-[#191A18] border border-[#41413B] text-[#F5F0E7]"
                  >
                    {task}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
