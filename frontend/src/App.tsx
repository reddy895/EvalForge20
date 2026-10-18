import { useState, useEffect } from 'react';
import type { NavRoute } from './types/navigation';
import { api } from './api/client';
import { ToastProvider } from './context/ToastContext';
import { Sidebar } from './components/shell/Sidebar';
import { TopBar } from './components/shell/TopBar';
import { MobileDrawer } from './components/shell/MobileDrawer';
import { ImportDatasetModal } from './components/datasets/ImportDatasetModal';

// Pages
import { OverviewPage } from './pages/OverviewPage';
import { RunsPage } from './pages/RunsPage';
import { RunDetailPage } from './pages/RunDetailPage';
import { NewEvalPage } from './pages/NewEvalPage';
import { ComparePage } from './pages/ComparePage';
import { DatasetsPage } from './pages/DatasetsPage';
import { ProvidersPage } from './pages/ProvidersPage';
import { EvaluatorsPage } from './pages/EvaluatorsPage';
import { ReportsPage } from './pages/ReportsPage';
import { RagEvalPage } from './pages/RagEvalPage';
import { AgentEvalPage } from './pages/AgentEvalPage';
import { TaskAnalysisPage } from './pages/TaskAnalysisPage';
import { SettingsPage } from './pages/SettingsPage';

export function AppContent() {
  const [currentRoute, setCurrentRoute] = useState<NavRoute>('overview');
  const [activeRunId, setActiveRunId] = useState<string>('run_851c7adf7d6a');
  const [currentWorkspace, setCurrentWorkspace] = useState<string>('reddy895/EvalForge20');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState<boolean>(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);

  // System Diagnostics
  const [ollamaConnected, setOllamaConnected] = useState<boolean>(false);
  const [systemReady, setSystemReady] = useState<boolean>(true);

  const checkStatus = async () => {
    try {
      const [readyRes, ollamaRes] = await Promise.all([
        api.getReadiness().catch(() => null),
        api.getOllamaStatus().catch(() => null),
      ]);
      setSystemReady(readyRes?.database === 'connected');
      setOllamaConnected(Boolean(ollamaRes?.connected));
    } catch {
      setSystemReady(false);
      setOllamaConnected(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleNavigate = (route: NavRoute, runId?: string) => {
    setCurrentRoute(route);
    if (runId) {
      setActiveRunId(runId);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const renderActivePage = () => {
    switch (currentRoute) {
      case 'overview':
        return <OverviewPage onNavigate={handleNavigate} />;
      case 'runs':
        return <RunsPage onNavigate={handleNavigate} />;
      case 'run-detail':
        return <RunDetailPage runId={activeRunId} onNavigate={handleNavigate} />;
      case 'new-eval':
        return <NewEvalPage onNavigate={handleNavigate} />;
      case 'compare':
        return <ComparePage />;
      case 'datasets':
        return (
          <DatasetsPage
            onOpenImportModal={() => setIsImportModalOpen(true)}
          />
        );
      case 'catalog':
        return <ProvidersPage />;
      case 'task-analysis':
        return <TaskAnalysisPage />;
      case 'providers':
        return <ProvidersPage />;
      case 'evaluators':
        return <EvaluatorsPage />;
      case 'reports':
        return <ReportsPage />;
      case 'rag':
        return <RagEvalPage />;
      case 'agents':
        return <AgentEvalPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <OverviewPage onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="app-container">
      {/* Desktop Sidebar (hidden on mobile) */}
      <div className="hide-on-mobile">
        <Sidebar
          currentRoute={currentRoute}
          onRouteChange={handleNavigate}
          systemReady={systemReady}
        />
      </div>

      {/* Mobile Drawer */}
      <MobileDrawer
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        currentRoute={currentRoute}
        onRouteChange={handleNavigate}
      />

      {/* Main Wrapper */}
      <div className="main-wrapper">
        <TopBar
          currentWorkspace={currentWorkspace}
          onWorkspaceChange={setCurrentWorkspace}
          onToggleMobileMenu={() => setIsMobileMenuOpen(true)}
          ollamaConnected={ollamaConnected}
          onRefreshStatus={checkStatus}
        />

        <main className="main-content" id="main-content" role="main">
          {renderActivePage()}
        </main>
      </div>

      {/* Global Import Dataset Modal */}
      <ImportDatasetModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={() => {
          checkStatus();
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}
