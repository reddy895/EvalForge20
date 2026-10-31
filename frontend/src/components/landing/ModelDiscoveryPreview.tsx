import React, { useState, useMemo } from 'react';
import { SAMPLE_MODELS } from '../../data/models';
import { ModelProfile, NavRoute } from '../../types';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { SearchInput } from '../ui/Input';
import { ArrowRight, Cpu, Zap, HardDrive, CheckCircle2, SlidersHorizontal } from 'lucide-react';

interface ModelDiscoveryPreviewProps {
  onRouteChange: (route: NavRoute) => void;
  onSelectModel: (model: ModelProfile) => void;
  onAddToCompare: (modelId: string) => void;
  compareModelIds: string[];
}

export const ModelDiscoveryPreview: React.FC<ModelDiscoveryPreviewProps> = ({
  onRouteChange,
  onSelectModel,
  onAddToCompare,
  compareModelIds,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTask, setSelectedTask] = useState<string>('all');

  const taskFilters = [
    { id: 'all', label: 'All Models' },
    { id: 'coding', label: 'Code Generation' },
    { id: 'reasoning', label: 'Math & Reasoning' },
    { id: 'structured_json', label: 'JSON Extraction' },
    { id: 'tool_calling', label: 'Agent Tools' },
  ];

  const filteredModels = useMemo(() => {
    return SAMPLE_MODELS.filter((model) => {
      const matchesSearch =
        searchQuery === '' ||
        model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.provider.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.family.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesTask =
        selectedTask === 'all' ||
        model.recommended_tasks.some((t) => t.toLowerCase().includes(selectedTask.toLowerCase()));

      return matchesSearch && matchesTask;
    }).slice(0, 6);
  }, [searchQuery, selectedTask]);

  return (
    <section id="discovery" className="py-24 px-4 sm:px-6 lg:px-8 2xl:px-12 w-full">
      <div className="w-full max-w-7xl mx-auto">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
        <div className="flex flex-col gap-3">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#14B8A6]">
            <SlidersHorizontal size={14} />
            <span>MODEL DISCOVERY</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
            Curated Model Intelligence
          </h2>
          <p className="text-sm sm:text-base text-[#A6A49D] max-w-xl">
            Filter, inspect hardware footprints, and verify empirical benchmark metrics across
            weights optimized for local workstations and production servers.
          </p>
        </div>

        <Button
          variant="outline"
          onClick={() => onRouteChange('models')}
          iconRight={<ArrowRight size={14} />}
        >
          View Full Catalog ({SAMPLE_MODELS.length})
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-3 rounded-2xl bg-[#242522] border border-[#41413B] mb-8">
        <div className="w-full sm:max-w-xs">
          <SearchInput
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
            placeholder="Search by name, provider..."
          />
        </div>

        {/* Task filter pill group */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {taskFilters.map((tf) => {
            const isSelected = selectedTask === tf.id;
            return (
              <button
                key={tf.id}
                onClick={() => setSelectedTask(tf.id)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-[#0D9488] text-[#191A18] font-semibold shadow-sm'
                    : 'bg-[#191A18] text-[#A6A49D] hover:text-[#F5F0E7] border border-[#41413B]'
                }`}
              >
                {tf.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredModels.map((model) => {
          const isCompared = compareModelIds.includes(model.id);
          const topScore = model.benchmarks[0];

          return (
            <Card
              key={model.id}
              hoverable
              className="group flex flex-col justify-between"
            >
              <div>
                {/* Card Top Row: Badges & Provider */}
                <CardHeader>
                  <div className="flex flex-col">
                    <span className="text-[11px] font-mono text-[#A6A49D] tracking-wide">
                      {model.provider}
                    </span>
                    <CardTitle className="text-lg group-hover:text-[#14B8A6] transition-colors mt-0.5">
                      {model.name}
                    </CardTitle>
                  </div>
                  <Badge variant={model.is_local ? 'installed' : 'outline'} size="sm">
                    {model.is_local ? 'Ollama' : 'Cloud'}
                  </Badge>
                </CardHeader>

                {/* Card Description */}
                <CardBody className="mt-2 text-xs text-[#A6A49D] line-clamp-2">
                  {model.description}
                </CardBody>

                {/* Specs Pill Matrix */}
                <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-[#41413B]/60 text-xs font-mono">
                  <div className="flex items-center gap-1.5 text-[#F5F0E7]">
                    <Cpu size={13} className="text-[#14B8A6]" />
                    <span>{model.parameter_count} params</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[#F5F0E7]">
                    <Zap size={13} className="text-[#14B8A6]" />
                    <span>{(model.context_window / 1024).toFixed(0)}k context</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[#A6A49D]">
                    <HardDrive size={13} className="text-[#A6A49D]" />
                    <span>Min {model.hardware.min_ram_gb} GB RAM</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[#A6A49D]">
                    <span className="text-[10px] text-[#78766F] font-sans">Quant:</span>
                    <span>{model.quantization || 'FP16'}</span>
                  </div>
                </div>

                {/* Top Benchmark Metric */}
                {topScore && (
                  <div className="mt-4 p-2.5 rounded-xl bg-[#191A18] border border-[#41413B] flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs text-[#A6A49D]">
                      <CheckCircle2 size={13} className="text-[#68B587]" />
                      <span>{topScore.benchmark_name}</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-[#F5F0E7]">
                      {topScore.score.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Card Footer Actions */}
              <div className="flex items-center gap-2 pt-4 mt-4 border-t border-[#41413B]/60">
                <Button
                  size="sm"
                  variant="secondary"
                  className="flex-1"
                  onClick={() => onSelectModel(model)}
                >
                  Profile
                </Button>
                <Button
                  size="sm"
                  variant={isCompared ? 'primary' : 'outline'}
                  onClick={() => onAddToCompare(model.id)}
                >
                  {isCompared ? 'Compared' : 'Compare'}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
      </div>
    </section>
  );
};
