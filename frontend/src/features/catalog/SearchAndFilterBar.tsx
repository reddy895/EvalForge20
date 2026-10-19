import React from 'react';
import { Search, X, Filter, Sparkles } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import './SearchAndFilterBar.css';

interface SearchAndFilterBarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedProvider: string;
  onProviderChange: (p: string) => void;
  selectedTask: string;
  onTaskChange: (t: string) => void;
  onlyInstalled: boolean;
  onOnlyInstalledToggle: () => void;
  sortBy: string;
  onSortChange: (s: string) => void;
  onOpenRecommendationModal: () => void;
  totalModels: number;
}

export const SearchAndFilterBar: React.FC<SearchAndFilterBarProps> = ({
  searchQuery,
  onSearchChange,
  selectedProvider,
  onProviderChange,
  selectedTask,
  onTaskChange,
  onlyInstalled,
  onOnlyInstalledToggle,
  sortBy,
  onSortChange,
  onOpenRecommendationModal,
  totalModels,
}) => {
  return (
    <div className="catalog-toolbar">
      {/* Top Search & Recommendation Assistant Row */}
      <div className="search-row">
        <div className="search-input-wrapper">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Search models by name, architecture, task (e.g. 'qwen', 'llama', 'coding', 'json')..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          {searchQuery && (
            <button className="clear-search-btn" onClick={() => onSearchChange('')}>
              <X size={14} />
            </button>
          )}
        </div>

        <Button
          variant="primary"
          onClick={onOpenRecommendationModal}
          iconLeft={<Sparkles size={15} />}
        >
          Model Finder Assistant
        </Button>
      </div>

      {/* Filter Chips & Sort Controls Row */}
      <div className="filter-controls-row">
        <div className="filter-group">
          <Filter size={14} className="filter-icon" />

          {/* Provider Filter */}
          <select
            className="filter-select"
            value={selectedProvider}
            onChange={(e) => onProviderChange(e.target.value)}
          >
            <option value="">All Providers</option>
            <option value="Qwen">Qwen / Alibaba</option>
            <option value="Meta">Meta AI</option>
            <option value="DeepSeek">DeepSeek AI</option>
            <option value="Google">Google</option>
            <option value="Microsoft">Microsoft</option>
            <option value="OpenAI">OpenAI</option>
            <option value="Anthropic">Anthropic</option>
          </select>

          {/* Task Filter */}
          <select
            className="filter-select"
            value={selectedTask}
            onChange={(e) => onTaskChange(e.target.value)}
          >
            <option value="">All Tasks</option>
            <option value="coding">Coding & Synthesis</option>
            <option value="reasoning">Math & Logic Reasoning</option>
            <option value="structured_json">Structured JSON Extraction</option>
            <option value="rag">Retrieval-Augmented Generation (RAG)</option>
            <option value="agent">Tool Use & Agents</option>
            <option value="local_edge">Lightweight Local Edge</option>
          </select>

          {/* Only Installed Toggle */}
          <label className="filter-checkbox-label">
            <input
              type="checkbox"
              className="filter-checkbox"
              checked={onlyInstalled}
              onChange={onOnlyInstalledToggle}
            />
            <span>Installed Locally in Ollama</span>
          </label>
        </div>

        <div className="sort-group">
          <span className="results-count font-mono">{totalModels} models</span>
          <span className="sort-label">Sort:</span>
          <select
            className="filter-select sort-select"
            value={sortBy}
            onChange={(e) => onSortChange(e.target.value)}
          >
            <option value="recommended">Recommended & Installed</option>
            <option value="benchmark">Benchmark Score (High to Low)</option>
            <option value="context">Context Window (Largest)</option>
            <option value="ram">System RAM (Lowest First)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
