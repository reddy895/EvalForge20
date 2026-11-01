import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { NavigationSidebar, NavigationTab } from './components/layout/NavigationSidebar';
import {
  PlaygroundView,
  ExperimentsView,
  ModelsView,
  BenchmarksView,
  DatasetsView,
  LeaderboardView,
  SettingsView,
} from './pages';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('playground');

  return (
    <div className="h-screen w-screen flex flex-col bg-[#F8FAFC] text-[#111827] overflow-hidden font-sans">
      {/* GLOBAL HEADER WITH OLLAMA & BACKEND HEALTH */}
      <Header activeTab={activeTab} />

      {/* MAIN CONTAINER: SIDEBAR + CONTENT VIEW */}
      <div className="flex-1 flex overflow-hidden">
        <NavigationSidebar activeTab={activeTab} onTabChange={setActiveTab} />

        <main className="flex-1 flex flex-col overflow-auto bg-[#F8FAFC]">
          {activeTab === 'playground' && <PlaygroundView />}
          {activeTab === 'experiments' && <ExperimentsView />}
          {activeTab === 'models' && <ModelsView />}
          {activeTab === 'benchmarks' && <BenchmarksView />}
          {activeTab === 'datasets' && <DatasetsView />}
          {activeTab === 'leaderboard' && <LeaderboardView />}
          {activeTab === 'settings' && <SettingsView />}
        </main>
      </div>
    </div>
  );
};

export default App;
