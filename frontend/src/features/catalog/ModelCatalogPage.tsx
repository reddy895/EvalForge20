import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import type { ModelSummary } from '../../types';
import { ModelCard } from './ModelCard';
import { SearchAndFilterBar } from './SearchAndFilterBar';
import { TaskRecommendationModal } from './TaskRecommendationModal';

interface ModelCatalogPageProps {
  onSelectModel: (modelId: string) => void;
  onCompareModel: (modelId: string) => void;
  onEvaluateModel: (modelTag: string) => void;
  comparingModelIds?: string[];
}

export const ModelCatalogPage: React.FC<ModelCatalogPageProps> = ({
  onSelectModel,
  onCompareModel,
  onEvaluateModel,
  comparingModelIds = [],
}) => {
  const [models, setModels] = useState<ModelSummary[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedTask, setSelectedTask] = useState<string>('');
  const [onlyInstalled, setOnlyInstalled] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<string>('recommended');

  const [isRecommendationModalOpen, setIsRecommendationModalOpen] = useState<boolean>(false);

  const fetchCatalog = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listModels({
        query: searchQuery || undefined,
        provider: selectedProvider || undefined,
        task: selectedTask || undefined,
        is_installed: onlyInstalled ? true : undefined,
        sort_by: sortBy,
      });
      setModels(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load model catalog');
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, selectedProvider, selectedTask, onlyInstalled, sortBy]);

  useEffect(() => {
    fetchCatalog();
  }, [fetchCatalog]);

  const localCount = models.filter((m) => m.is_local).length;
  const installedCount = models.filter((m) => m.is_installed).length;

  return (
    <div className="page-container catalog-page">
      {/* Page Hero */}
      <div className="catalog-hero">
        <h1 className="hero-title">Model Intelligence & Catalog</h1>
        <p className="hero-subtitle">
          Search, compare capabilities, and inspect verified benchmarks for open-weights and frontier AI models.
          Run reproducible evaluations locally on your hardware with Ollama.
        </p>

        <div className="hero-stats-row">
          <div className="hero-stat-pill">
            <span className="stat-label">Catalog Models:</span>
            <span className="stat-val font-mono">{models.length}</span>
          </div>
          <div className="hero-stat-pill">
            <span className="stat-label">Local Edge Models:</span>
            <span className="stat-val font-mono">{localCount}</span>
          </div>
          <div className="hero-stat-pill installed">
            <span className="stat-label">Installed in Ollama:</span>
            <span className="stat-val font-mono font-bold">{installedCount}</span>
          </div>
        </div>
      </div>

      {/* Search & Filter Controls */}
      <SearchAndFilterBar
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedProvider={selectedProvider}
        onProviderChange={setSelectedProvider}
        selectedTask={selectedTask}
        onTaskChange={setSelectedTask}
        onlyInstalled={onlyInstalled}
        onOnlyInstalledToggle={() => setOnlyInstalled(!onlyInstalled)}
        sortBy={sortBy}
        onSortChange={setSortBy}
        onOpenRecommendationModal={() => setIsRecommendationModalOpen(true)}
        totalModels={models.length}
      />

      {/* Error state */}
      {error && <div className="error-banner">{error}</div>}

      {/* Loading state */}
      {isLoading && (
        <div className="loading-state">
          <span className="spinner" />
          <p>Discovering models and verifying local Ollama daemon status...</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && models.length === 0 && (
        <div className="empty-state">
          <h3>No models matched your search criteria</h3>
          <p>Try clearing filters or checking for typos.</p>
        </div>
      )}

      {/* Model Cards Grid */}
      {!isLoading && models.length > 0 && (
        <div className="models-grid">
          {models.map((model) => (
            <ModelCard
              key={model.id}
              model={model}
              onSelect={onSelectModel}
              onCompare={onCompareModel}
              onEvaluate={onEvaluateModel}
              isComparing={comparingModelIds.includes(model.id)}
            />
          ))}
        </div>
      )}

      {/* Recommendation Assistant Modal */}
      <TaskRecommendationModal
        isOpen={isRecommendationModalOpen}
        onClose={() => setIsRecommendationModalOpen(false)}
        onSelectModel={onSelectModel}
        onEvaluateModel={onEvaluateModel}
      />
    </div>
  );
};
