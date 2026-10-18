import React, { useEffect, useState, useMemo } from 'react';
import { Search, CheckCircle2, Cpu, Cloud } from 'lucide-react';
import { api } from '../../api/client';
import type { CatalogModel } from '../../api/types';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import './ModelSelector.css';

interface ModelSelectorProps {
  selectedModelId: string;
  selectedProvider: string;
  onSelectModel: (model: {
    model_identifier: string;
    provider_name: string;
    target_name?: string;
  }) => void;
}

const PROVIDER_OPTIONS = [
  { id: 'all', label: 'All Providers' },
  { id: 'ollama', label: 'Ollama (Local)' },
  { id: 'openai', label: 'OpenAI' },
  { id: 'anthropic', label: 'Anthropic' },
  { id: 'gemini', label: 'Google Gemini' },
  { id: 'nvidia', label: 'NVIDIA NIM' },
  { id: 'mock', label: 'Mock Target' },
];

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModelId,
  selectedProvider,
  onSelectModel,
}) => {
  const [catalog, setCatalog] = useState<CatalogModel[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [providerFilter, setProviderFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isManualMode, setIsManualMode] = useState<boolean>(false);
  const [manualModelId, setManualModelId] = useState<string>(selectedModelId);
  const [manualProvider, setManualProvider] = useState<string>(selectedProvider || 'ollama');

  useEffect(() => {
    const fetchCatalog = async () => {
      setIsLoading(true);
      try {
        const models = await api.listCatalogModels();
        setCatalog(models);
      } catch {
        // Fallback default models if catalog endpoint is offline
        setCatalog([
          {
            name: 'Qwen 2.5 3B Instruct',
            provider: 'ollama',
            model_identifier: 'qwen2.5:3b',
            is_local: true,
            modalities: ['text'],
            supports_tools: true,
            supports_structured_output: true,
            connection_status: 'online',
          },
          {
            name: 'Llama 3.2 3B Instruct',
            provider: 'ollama',
            model_identifier: 'llama3.2:3b',
            is_local: true,
            modalities: ['text'],
            supports_tools: true,
            supports_structured_output: true,
            connection_status: 'online',
          },
          {
            name: 'GPT-4o Mini',
            provider: 'openai',
            model_identifier: 'gpt-4o-mini',
            is_local: false,
            modalities: ['text'],
            supports_tools: true,
            supports_structured_output: true,
            connection_status: 'configured',
          },
          {
            name: 'Claude 3.5 Sonnet',
            provider: 'anthropic',
            model_identifier: 'claude-3-5-sonnet-20241022',
            is_local: false,
            modalities: ['text'],
            supports_tools: true,
            supports_structured_output: true,
            connection_status: 'configured',
          },
          {
            name: 'Deterministic Mock Target',
            provider: 'mock',
            model_identifier: 'mock-model-v1',
            is_local: true,
            modalities: ['text'],
            supports_tools: false,
            supports_structured_output: true,
            connection_status: 'online',
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCatalog();
  }, []);

  const filteredModels = useMemo(() => {
    return catalog.filter((m) => {
      const matchesProvider =
        providerFilter === 'all' || m.provider.toLowerCase() === providerFilter.toLowerCase();
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        m.name.toLowerCase().includes(q) ||
        m.model_identifier.toLowerCase().includes(q) ||
        m.provider.toLowerCase().includes(q);

      return matchesProvider && matchesSearch;
    });
  }, [catalog, providerFilter, searchQuery]);

  const handleSelect = (model: CatalogModel) => {
    onSelectModel({
      model_identifier: model.model_identifier,
      provider_name: model.provider,
      target_name: `${model.provider}-${model.model_identifier.replace(/[^a-zA-Z0-9_-]/g, '_')}`,
    });
  };

  const handleApplyManual = () => {
    if (!manualModelId.trim()) return;
    onSelectModel({
      model_identifier: manualModelId.trim(),
      provider_name: manualProvider,
      target_name: `${manualProvider}-${manualModelId.trim().replace(/[^a-zA-Z0-9_-]/g, '_')}`,
    });
  };

  return (
    <div className="model-selector-container">
      <div className="flex-between">
        <span className="text-label" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          Model Selection Catalog
        </span>
        <button
          type="button"
          className="custom-entry-toggle"
          onClick={() => setIsManualMode(!isManualMode)}
        >
          {isManualMode ? 'Browse Catalog Models' : 'Enter Custom Model Identifier'}
        </button>
      </div>

      {isManualMode ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="manual-provider-select">
                Target Provider
              </label>
              <select
                id="manual-provider-select"
                className="input-control"
                value={manualProvider}
                onChange={(e) => setManualProvider(e.target.value)}
              >
                <option value="ollama">Ollama (Local LLM)</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="gemini">Google Gemini</option>
                <option value="nvidia">NVIDIA NIM</option>
                <option value="custom_openai">Custom OpenAI-Compatible</option>
                <option value="mock">Deterministic Mock Target</option>
              </select>
            </div>
            <Input
              label="Model Identifier"
              required
              isMonospace
              value={manualModelId}
              onChange={(e) => setManualModelId(e.target.value)}
              placeholder="e.g. llama3.3:70b or gpt-4o"
            />
          </div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            style={{ alignSelf: 'flex-start' }}
            onClick={handleApplyManual}
          >
            Apply Identifier
          </button>
        </div>
      ) : (
        <div className="model-selector-toolbar">
          <div className="model-search-wrap">
            <Search size={14} className="model-search-icon" />
            <input
              type="text"
              className="model-search-input"
              placeholder="Search models by name, architecture, or identifier..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="provider-filters-row">
            {PROVIDER_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                type="button"
                className={`provider-filter-pill ${providerFilter === opt.id ? 'active' : ''}`}
                onClick={() => setProviderFilter(opt.id)}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <div className="model-selector-list">
            {isLoading ? (
              <div style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '11px', textAlign: 'center' }}>
                Loading model catalog...
              </div>
            ) : filteredModels.length === 0 ? (
              <div style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '11px', textAlign: 'center' }}>
                No models matched "{searchQuery}". You can enter a custom identifier above.
              </div>
            ) : (
              filteredModels.map((m) => {
                const isSelected =
                  m.model_identifier === selectedModelId &&
                  m.provider.toLowerCase() === selectedProvider.toLowerCase();

                return (
                  <div
                    key={`${m.provider}-${m.model_identifier}`}
                    className={`model-selector-item ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelect(m)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className="model-item-main">
                      <div className="model-item-title">
                        {m.is_local ? <Cpu size={13} color="var(--accent-primary)" /> : <Cloud size={13} />}
                        <span>{m.name}</span>
                        <Badge variant={m.is_local ? 'neutral' : 'accent'}>
                          {m.provider.toUpperCase()}
                        </Badge>
                      </div>
                      <span className="model-item-subtitle">{m.model_identifier}</span>
                    </div>

                    <div className="model-item-meta">
                      {m.is_local ? (
                        <span style={{ color: 'var(--status-success)', fontSize: '10px' }}>
                          $0.00 / Local
                        </span>
                      ) : m.pricing ? (
                        <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>
                          ${m.pricing.input_price_per_m}/M in · ${m.pricing.output_price_per_m}/M out
                        </span>
                      ) : null}

                      {isSelected && <CheckCircle2 size={14} color="var(--accent-primary)" />}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
