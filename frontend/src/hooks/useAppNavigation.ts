import { useState, useEffect, useCallback } from 'react';
import { NavigationTab } from '../components/layout/NavigationSidebar';

interface NavigationState {
  activeTab: NavigationTab;
  activeRunId: string | null;
}

function parseLocation(): NavigationState {
  const path = window.location.pathname;

  // Match /evaluations/:runId or /evaluations
  const evalMatch = path.match(/^\/evaluations(?:\/([^/?#]+))?/);
  if (evalMatch) {
    const runId = evalMatch[1] || null;
    return {
      activeTab: 'results',
      activeRunId: runId,
    };
  }

  // Check query param fallback ?runId=...
  const params = new URLSearchParams(window.location.search);
  const qRunId = params.get('runId');
  if (qRunId) {
    return {
      activeTab: 'results',
      activeRunId: qRunId,
    };
  }

  // Check known tabs
  const tabName = path.replace(/^\//, '').split('/')[0] as NavigationTab;
  const validTabs: NavigationTab[] = [
    'playground',
    'results',
    'experiments',
    'models',
    'benchmarks',
    'datasets',
    'leaderboard',
    'settings',
  ];

  if (validTabs.includes(tabName)) {
    return {
      activeTab: tabName,
      activeRunId: null,
    };
  }

  return {
    activeTab: 'playground',
    activeRunId: null,
  };
}

export function useAppNavigation() {
  const [navState, setNavState] = useState<NavigationState>(() => parseLocation());

  useEffect(() => {
    const handlePopState = () => {
      setNavState(parseLocation());
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateTo = useCallback((tab: NavigationTab, runId?: string | null) => {
    let targetPath = '/';
    let newRunId: string | null = null;

    if (tab === 'results') {
      newRunId = runId || navState.activeRunId || null;
      targetPath = newRunId ? `/evaluations/${newRunId}` : '/evaluations';
    } else if (tab === 'playground') {
      targetPath = '/';
    } else {
      targetPath = `/${tab}`;
    }

    if (window.location.pathname !== targetPath) {
      window.history.pushState({ tab, runId: newRunId }, '', targetPath);
    }

    setNavState({
      activeTab: tab,
      activeRunId: newRunId,
    });
  }, [navState.activeRunId]);

  return {
    activeTab: navState.activeTab,
    activeRunId: navState.activeRunId,
    navigateTo,
  };
}

