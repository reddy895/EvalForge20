import React, { useState, useMemo, useEffect } from 'react';
import { SAMPLE_MODELS } from '../../data/models';
import { ModelProfile, NavRoute } from '../../types';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { SearchInput, Select } from '../ui/Input';
import { ModelProfileModal } from '../profile/ModelProfileModal';
import { api } from '../../services/api';
import { useToast } from '../ui/Toast';
import {
  LayoutGrid,
  List,
  SlidersHorizontal,
  Cpu,
  Zap,
  HardDrive,
  CheckCircle2,
  GitCompare,
  Play,
  RotateCcw,
  RefreshCw,
} from 'lucide-react';

interface ModelsPageProps {
  onRouteChange: (route: NavRoute) => void;
  onSelectModelForEvaluation: (modelId: string) => void;
  compareModelIds: string[];
  onToggleCompare: (modelId: string) => void;
}

export const ModelsPage: React.FC<ModelsPageProps> = ({
  onRouteChange,
  onSelectModelForEvaluation,
  compareModelIds,
  onToggleCompare,
}) => {
  const { info, success, error } = useToast();
  const [models, setModels] = useState<ModelProfile[]>(SAMPLE_MODELS);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [selectedTask, setSelectedTask] = useState<string>('all');
  const [selectedLicense, setSelectedLicense] = useState<string>('all');
  const [localOnly, setLocalOnly] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<'recommended' | 'benchmark' | 'context' | 'ram'>('recommended');

  const [activeProfileModel, setActiveProfileModel] = useState<ModelProfile | null>(null);

  useEffect(() => {
    let mounted = true;
    api
      .getModels()
      .then((res) => {
        if (mounted && res.models && res.models.length > 0) {
          setModels(res.models);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const handleSyncDiscovery = async () => {
    setIsRefreshing(true);
    info('Discovering Models', 'Scanning local Ollama daemon and inference registry...');
    try {
      await api.refreshModels();
      const res = await api.getModels();
      if (res.models && res.models.length > 0) {
        setModels(res.models);
        success('Catalog Synchronized', `Discovered ${res.total} models across local and cloud providers.`);
      }
    } catch (err: any) {
      error('Sync Failed', err?.message || 'Could not reach inference endpoints');
    } finally {
      setIsRefreshing(false);
    }
  };

  const providers = useMemo(() => {
    const set = new Set(models.map((m) => m.provider));
    return ['all', ...Array.from(set)];
  }, [models]);

  const filteredModels = useMemo(() => {
    let result = models.filter((model) => {
      const matchesSearch =
        searchQuery === '' ||
        model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.provider.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.family.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.description.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesProvider =
        selectedProvider === 'all' || model.provider === selectedProvider;

      const matchesTask =
        selectedTask === 'all' ||
        model.recommended_tasks.some((t) => t.toLowerCase().includes(selectedTask.toLowerCase()));

      const matchesLicense =
        selectedLicense === 'all' || model.license.toLowerCase().includes(selectedLicense.toLowerCase());

      const matchesLocal = !localOnly || model.is_local;

      return matchesSearch && matchesProvider && matchesTask && matchesLicense && matchesLocal;
    });

    // Sorting
    result.sort((a, b) => {
      if (sortBy === 'benchmark') {
        const scoreA = a.benchmarks[0]?.score || 0;
        const scoreB = b.benchmarks[0]?.score || 0;
        return scoreB - scoreA;
      }
      if (sortBy === 'context') {
        return b.context_window - a.context_window;
      }
      if (sortBy === 'ram') {
        return a.hardware.min_ram_gb - b.hardware.min_ram_gb;
      }
      return 0; // default order
    });

    return result;
  }, [models, searchQuery, selectedProvider, selectedTask, selectedLicense, localOnly, sortBy]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedProvider('all');
    setSelectedTask('all');
    setSelectedLicense('all');
    setLocalOnly(false);
    setSortBy('recommended');
  };

  return (
    <div className="py-10 px-4 sm:px-8 lg:px-12 2xl:px-16 w-full flex flex-col gap-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#41413B]">
        <div className="flex flex-col gap-2">
          <div className="inline-flex items-center gap-2 text-xs font-mono text-[#14B8A6]">
            <Cpu size={14} />
            <span>MODEL INTELLIGENCE CATALOG</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F0E7]">
            Model Catalog
          </h1>
          <p className="text-sm text-[#A6A49D] max-w-xl">
            Explore verified specifications, hardware memory requirements, and empirical benchmark
            evaluations across {models.length} curated open-source, local Ollama, and cloud models.
          </p>
        </div>

        {/* View Switcher & Action */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSyncDiscovery}
            iconLeft={<RefreshCw size={13} className={isRefreshing ? 'animate-spin' : ''} />}
          >
            Sync Ollama & APIs
          </Button>

          <div className="flex items-center rounded-full bg-[#191A18] p-1 border border-[#41413B]">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-full transition-all cursor-pointer ${
                viewMode === 'grid'
                  ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                  : 'text-[#A6A49D] hover:text-[#F5F0E7]'
              }`}
              title="Grid View"
            >
              <LayoutGrid size={16} />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-2 rounded-full transition-all cursor-pointer ${
                viewMode === 'table'
                  ? 'bg-[#242522] text-[#F5F0E7] shadow-sm'
                  : 'text-[#A6A49D] hover:text-[#F5F0E7]'
              }`}
              title="Table View"
            >
              <List size={16} />
            </button>
          </div>

          {compareModelIds.length > 0 && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onRouteChange('compare')}
              iconLeft={<GitCompare size={14} />}
            >
              Compare ({compareModelIds.length})
            </Button>
          )}
        </div>
      </div>

      {/* Filter and Control Bar */}
      <div className="p-5 rounded-3xl bg-[#242522] border border-[#41413B] flex flex-col gap-4 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <SearchInput
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
            placeholder="Search models..."
          />

          <Select
            label=""
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            options={providers.map((p) => ({
              value: p,
              label: p === 'all' ? 'All Providers' : p,
            }))}
          />

          <Select
            label=""
            value={selectedTask}
            onChange={(e) => setSelectedTask(e.target.value)}
            options={[
              { value: 'all', label: 'All Tasks & Workloads' },
              { value: 'coding', label: 'Code Generation' },
              { value: 'reasoning', label: 'Math & Reasoning' },
              { value: 'structured_json', label: 'JSON Extraction' },
              { value: 'tool_calling', label: 'Agent Tools' },
            ]}
          />

          <Select
            label=""
            value={sortBy}
            onChange={(e) =>
              setSortBy(e.target.value as 'recommended' | 'benchmark' | 'context' | 'ram')
            }
            options={[
              { value: 'recommended', label: 'Sort: Recommended' },
              { value: 'benchmark', label: 'Sort: Top Benchmark Score' },
              { value: 'context', label: 'Sort: Largest Context' },
              { value: 'ram', label: 'Sort: Lowest RAM Req' },
            ]}
          />
        </div>

        {/* Secondary filters row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#41413B]/60 text-xs">
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer select-none text-[#F5F0E7]">
              <input
                type="checkbox"
                checked={localOnly}
                onChange={(e) => setLocalOnly(e.target.checked)}
                className="w-4 h-4 rounded text-[#14B8A6] bg-[#191A18] border-[#41413B] focus:ring-0 focus:ring-offset-0 cursor-pointer"
              />
              <span>Local Ollama models only</span>
            </label>

            <span className="text-[#A6A49D]">
              Showing <strong className="text-[#F5F0E7]">{filteredModels.length}</strong> of{' '}
              {SAMPLE_MODELS.length} models
            </span>
          </div>

          {(searchQuery || selectedProvider !== 'all' || selectedTask !== 'all' || localOnly) && (
            <button
              onClick={handleResetFilters}
              className="flex items-center gap-1.5 text-[#14B8A6] hover:underline cursor-pointer"
            >
              <RotateCcw size={12} /> Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Empty State */}
      {filteredModels.length === 0 ? (
        <div className="py-20 px-6 rounded-3xl bg-[#242522] border border-[#41413B] text-center flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#191A18] border border-[#41413B] flex items-center justify-center text-[#14B8A6]">
            <SlidersHorizontal size={20} />
          </div>
          <h3 className="text-lg font-semibold text-[#F5F0E7]">No matching models found</h3>
          <p className="text-sm text-[#A6A49D] max-w-sm">
            We couldn't find any models matching your active filter criteria. Try resetting your search
            or adjusting your filters.
          </p>
          <Button variant="secondary" size="sm" onClick={handleResetFilters}>
            Reset All Filters
          </Button>
        </div>
      ) : viewMode === 'grid' ? (
        /* Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredModels.map((model) => {
            const isCompared = compareModelIds.includes(model.id);
            const topScore = model.benchmarks[0];

            return (
              <Card key={model.id} hoverable className="group flex flex-col justify-between">
                <div>
                  <CardHeader>
                    <div className="flex flex-col">
                      <span className="text-[11px] font-mono text-[#A6A49D]">{model.provider}</span>
                      <CardTitle className="text-lg group-hover:text-[#14B8A6] transition-colors mt-0.5">
                        {model.name}
                      </CardTitle>
                    </div>
                    <Badge variant={model.is_local ? 'installed' : 'outline'} size="sm">
                      {model.is_local ? 'Ollama' : 'Cloud'}
                    </Badge>
                  </CardHeader>

                  <CardBody className="mt-2 text-xs text-[#A6A49D] line-clamp-2">
                    {model.description}
                  </CardBody>

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

                  {/* Capability & Feature Badges */}
                  <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-[#41413B]/40">
                    {model.supports_structured_output && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-sans bg-[#0D9488]/10 text-[#14B8A6] border border-[#0D9488]/30">
                        JSON Schema
                      </span>
                    )}
                    {model.supports_tools && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-sans bg-[#0D9488]/10 text-[#14B8A6] border border-[#0D9488]/30">
                        Tool Calling
                      </span>
                    )}
                    {model.license && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-[#191A18] text-[#A6A49D] border border-[#41413B]">
                        {model.license}
                      </span>
                    )}
                  </div>

                  {topScore && (
                    <div className="mt-3 p-2.5 rounded-xl bg-[#191A18] border border-[#41413B] flex items-center justify-between">
                      <div className="flex items-center gap-1.5 text-xs text-[#A6A49D]">
                        <CheckCircle2 size={13} className="text-[#14B8A6]" />
                        <span>{topScore.benchmark_name}</span>
                      </div>
                      <span className="text-xs font-mono font-bold text-[#F5F0E7]">
                        {topScore.score.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 pt-4 mt-4 border-t border-[#41413B]/60">
                  <Button
                    size="sm"
                    variant="secondary"
                    className="flex-1"
                    onClick={() => setActiveProfileModel(model)}
                  >
                    Profile
                  </Button>
                  <Button
                    size="sm"
                    variant={isCompared ? 'primary' : 'outline'}
                    onClick={() => onToggleCompare(model.id)}
                  >
                    {isCompared ? 'Compared' : 'Compare'}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onSelectModelForEvaluation(model.id)}
                    title="Evaluate model"
                  >
                    <Play size={14} className="fill-current text-[#14B8A6]" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        /* Table View */
        <div className="rounded-3xl bg-[#242522] border border-[#41413B] overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#191A18] text-[#A6A49D] font-mono border-b border-[#41413B]">
                <tr>
                  <th className="p-4">Model Name</th>
                  <th className="p-4">Provider</th>
                  <th className="p-4">Parameters</th>
                  <th className="p-4">Context</th>
                  <th className="p-4">Min RAM</th>
                  <th className="p-4">Key Benchmark</th>
                  <th className="p-4">Pricing</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#41413B]/60 text-sm">
                {filteredModels.map((model) => {
                  const isCompared = compareModelIds.includes(model.id);
                  const topScore = model.benchmarks[0];

                  return (
                    <tr
                      key={model.id}
                      className="hover:bg-white/[0.02] transition-colors cursor-pointer"
                      onClick={() => setActiveProfileModel(model)}
                    >
                      <td className="p-4 font-semibold text-[#F5F0E7]">
                        <div className="flex items-center gap-2">
                          <span>{model.name}</span>
                          {model.is_local && (
                            <Badge variant="installed" size="sm">
                              Local
                            </Badge>
                          )}
                          {model.supports_structured_output && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-sans bg-[#0D9488]/10 text-[#14B8A6] border border-[#0D9488]/30">
                              JSON
                            </span>
                          )}
                          {model.supports_tools && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-sans bg-[#0D9488]/10 text-[#14B8A6] border border-[#0D9488]/30">
                              Tools
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-[#A6A49D]">{model.provider}</td>
                      <td className="p-4 font-mono text-[#F5F0E7]">{model.parameter_count}</td>
                      <td className="p-4 font-mono text-[#F5F0E7]">
                        {(model.context_window / 1024).toFixed(0)}k
                      </td>
                      <td className="p-4 font-mono text-[#A6A49D]">{model.hardware.min_ram_gb} GB</td>
                      <td className="p-4 font-mono">
                        {topScore ? (
                          <span className="text-[#14B8A6] font-semibold">
                            {topScore.score.toFixed(1)}% ({topScore.benchmark_name})
                          </span>
                        ) : (
                          <span className="text-[#78766F]">—</span>
                        )}
                      </td>
                      <td className="p-4 font-mono text-xs text-[#A6A49D]">
                        {model.pricing.is_free_local
                          ? 'Free (Local)'
                          : `$${model.pricing.input_cost_per_m?.toFixed(2)}/1M`}
                      </td>
                      <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant={isCompared ? 'primary' : 'outline'}
                            onClick={() => onToggleCompare(model.id)}
                          >

                            {isCompared ? 'Remove' : 'Compare'}
                          </Button>
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => onSelectModelForEvaluation(model.id)}
                            iconRight={<Play size={12} className="fill-current" />}
                          >
                            Eval
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Model Profile Modal */}
      <ModelProfileModal
        model={activeProfileModel}
        isOpen={activeProfileModel !== null}
        onClose={() => setActiveProfileModel(null)}
        onCompare={(id) => onToggleCompare(id)}
        onEvaluate={(id) => onSelectModelForEvaluation(id)}
        isCompared={activeProfileModel ? compareModelIds.includes(activeProfileModel.id) : false}
      />
    </div>
  );
};
