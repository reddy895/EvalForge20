import React, { useState, useEffect } from 'react';
import { NavRoute, ModelProfile, EvaluationRun } from '../../types';
import { Header } from './Header';
import { Footer } from './Footer';
import { LandingPage } from '../landing/LandingPage';
import { ModelsPage } from '../catalog/ModelsPage';
import { ComparePage } from '../comparison/ComparePage';
import { EvaluatePage } from '../evaluations/EvaluatePage';
import { HistoryPage } from '../history/HistoryPage';
import { AnalyticsPage } from '../analytics/AnalyticsPage';
import { ModelProfileModal } from '../profile/ModelProfileModal';
import { api } from '../../services/api';

export const AppShell: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState<NavRoute>('landing');
  const [compareModelIds, setCompareModelIds] = useState<string[]>([
    'qwen-2.5-1.5b-instruct',
    'qwen-2.5-3b-instruct',
  ]);
  const [selectedModelForEval, setSelectedModelForEval] = useState<string>('qwen-2.5-1.5b-instruct');
  const [selectedProfileModel, setSelectedProfileModel] = useState<ModelProfile | null>(null);
  const [historyRuns, setHistoryRuns] = useState<EvaluationRun[]>([]);

  useEffect(() => {
    // Fetch persisted evaluations from backend database
    api.getEvaluations({ limit: 50 })
      .then((runs) => {
        if (Array.isArray(runs) && runs.length > 0) {
          setHistoryRuns(runs);
        }
      })
      .catch(() => {});
  }, []);

  const handleRouteChange = (route: NavRoute) => {
    setCurrentRoute(route);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleToggleCompare = (modelId: string) => {
    setCompareModelIds((prev) => {
      if (prev.includes(modelId)) {
        return prev.filter((id) => id !== modelId);
      }
      if (prev.length >= 4) {
        return prev;
      }
      return [...prev, modelId];
    });
  };

  const handleClearCompare = () => {
    setCompareModelIds([]);
  };

  const handleSelectModelForEvaluation = (modelId: string) => {
    setSelectedModelForEval(modelId);
    setCurrentRoute('evaluate');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSaveToHistory = (run: EvaluationRun) => {
    setHistoryRuns((prev) => [run, ...prev]);
  };

  const handleClearHistory = () => {
    setHistoryRuns([]);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#191A18] text-[#F5F0E7] selection:bg-[#D9823B] selection:text-[#191A18]">
      {/* Top Floating Header */}
      <Header currentRoute={currentRoute} onRouteChange={handleRouteChange} />

      {/* Main Content View Switcher */}
      <main className="flex-1 w-full">
        {currentRoute === 'landing' && (
          <LandingPage
            onRouteChange={handleRouteChange}
            onSelectModel={(model) => setSelectedProfileModel(model)}
            onAddToCompare={handleToggleCompare}
            compareModelIds={compareModelIds}
          />
        )}

        {currentRoute === 'models' && (
          <ModelsPage
            onRouteChange={handleRouteChange}
            onSelectModelForEvaluation={handleSelectModelForEvaluation}
            compareModelIds={compareModelIds}
            onToggleCompare={handleToggleCompare}
          />
        )}

        {currentRoute === 'compare' && (
          <ComparePage
            compareModelIds={compareModelIds}
            onToggleCompare={handleToggleCompare}
            onClearCompare={handleClearCompare}
            onRouteChange={handleRouteChange}
            onSelectModelForEvaluation={handleSelectModelForEvaluation}
          />
        )}

        {currentRoute === 'evaluate' && (
          <EvaluatePage
            initialModelId={selectedModelForEval}
            onSaveToHistory={handleSaveToHistory}
            onRouteChange={handleRouteChange}
          />
        )}

        {currentRoute === 'history' && (
          <HistoryPage
            historyRuns={historyRuns}
            onClearHistory={handleClearHistory}
            onRouteChange={handleRouteChange}
          />
        )}

        {currentRoute === 'analytics' && (
          <AnalyticsPage onRouteChange={handleRouteChange} />
        )}
      </main>

      {/* Global Profile Modal for Landing selection */}
      <ModelProfileModal
        model={selectedProfileModel}
        isOpen={selectedProfileModel !== null}
        onClose={() => setSelectedProfileModel(null)}
        onCompare={handleToggleCompare}
        onEvaluate={handleSelectModelForEvaluation}
        isCompared={
          selectedProfileModel ? compareModelIds.includes(selectedProfileModel.id) : false
        }
      />

      {/* Footer */}
      <Footer onRouteChange={handleRouteChange} />
    </div>
  );
};
