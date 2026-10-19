import React, { useState, useEffect, useCallback } from 'react';
import type { NavRoute, OllamaStatusReport } from '../types';
import { api } from '../services/api';
import { Navigation } from './Navigation';
import { ModelCatalogPage } from '../features/catalog/ModelCatalogPage';
import { ModelProfilePage } from '../features/model-profile/ModelProfilePage';
import { ModelComparisonPage } from '../features/comparison/ModelComparisonPage';
import { LocalEvaluationPage } from '../features/evaluations/LocalEvaluationPage';
import { EvaluationHistoryPage } from '../features/evaluations/EvaluationHistoryPage';
import { SettingsPage } from '../features/settings/SettingsPage';

export const App: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState<NavRoute>('catalog');
  const [activeProfileModelId, setActiveProfileModelId] = useState<string | null>(null);
  const [evaluationModelId, setEvaluationModelId] = useState<string | null>(null);
  const [comparisonModelIds, setComparisonModelIds] = useState<string[]>([
    'llama-3.1-8b-instruct',
    'qwen-2.5-7b-instruct',
  ]);

  // System Diagnostics State
  const [backendOnline, setBackendOnline] = useState<boolean>(true);
  const [backendLatencyMs, setBackendLatencyMs] = useState<number | undefined>(undefined);
  const [ollamaReport, setOllamaReport] = useState<OllamaStatusReport | null>(null);

  const checkDiagnostics = useCallback(async () => {
    try {
      const [health, ollama] = await Promise.all([
        api.checkBackendHealth(),
        api.getOllamaReport().catch(() => null),
      ]);
      setBackendOnline(health.is_connected);
      setBackendLatencyMs(health.latency_ms);
      if (ollama) setOllamaReport(ollama);
    } catch {
      setBackendOnline(false);
    }
  }, []);

  useEffect(() => {
    checkDiagnostics();
    const timer = setInterval(checkDiagnostics, 15000);
    return () => clearInterval(timer);
  }, [checkDiagnostics]);

  const handleOpenProfile = (modelId: string) => {
    setActiveProfileModelId(modelId);
    setCurrentRoute('model-profile');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartComparison = (modelId: string) => {
    setComparisonModelIds((prev) => {
      if (!prev.includes(modelId)) {
        return [...prev.slice(0, 3), modelId];
      }
      return prev;
    });
    setCurrentRoute('compare');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartEvaluation = (modelId: string) => {
    setEvaluationModelId(modelId);
    setCurrentRoute('evaluate');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderContent = () => {
    switch (currentRoute) {
      case 'catalog':
        return (
          <ModelCatalogPage
            onSelectModel={handleOpenProfile}
            onCompareModel={handleStartComparison}
            onEvaluateModel={handleStartEvaluation}
          />
        );
      case 'model-profile':
        if (!activeProfileModelId) {
          return (
            <ModelCatalogPage
              onSelectModel={handleOpenProfile}
              onCompareModel={handleStartComparison}
              onEvaluateModel={handleStartEvaluation}
            />
          );
        }
        return (
          <ModelProfilePage
            modelId={activeProfileModelId}
            onBack={() => setCurrentRoute('catalog')}
            onCompare={handleStartComparison}
            onEvaluate={handleStartEvaluation}
          />
        );
      case 'compare':
        return (
          <ModelComparisonPage
            initialModelIds={comparisonModelIds}
            onNavigateToCatalog={() => setCurrentRoute('catalog')}
          />
        );
      case 'evaluate':
        return (
          <LocalEvaluationPage
            initialModelId={evaluationModelId}
            onNavigateToHistory={() => setCurrentRoute('history')}
          />
        );
      case 'history':
        return (
          <EvaluationHistoryPage
            onNewEvaluation={() => setCurrentRoute('evaluate')}
          />
        );
      case 'settings':
        return <SettingsPage />;
      default:
        return (
          <ModelCatalogPage
            onSelectModel={handleOpenProfile}
            onCompareModel={handleStartComparison}
            onEvaluateModel={handleStartEvaluation}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#171816] text-[#F0EEE6] flex flex-col font-sans selection:bg-[#E58B45]/20 selection:text-[#F0EEE6]">
      {/* Top minimal navigation */}
      <Navigation
        activeRoute={currentRoute}
        onRouteChange={(route) => {
          setCurrentRoute(route);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        ollamaStatus={ollamaReport}
        backendOnline={backendOnline}
        backendLatencyMs={backendLatencyMs}
        onRefreshHealth={checkDiagnostics}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderContent()}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#393A33] py-6 text-center text-xs text-[#A5A59A] bg-[#171816]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-semibold text-[#F0EEE6]">EvalForge20</span> &bull; Local-First LLM Intelligence & Evaluation Platform
          </div>
          <div>
            Verified Benchmarks &bull; Transparent Metrics &bull; Ollama Powered
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
