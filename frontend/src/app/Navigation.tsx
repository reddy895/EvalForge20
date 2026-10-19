import React from 'react';
import { Compass, Scale, PlayCircle, History, Settings, Cpu, HardDrive } from 'lucide-react';
import type { NavRoute, OllamaStatusReport } from '../types';

interface NavigationProps {
  currentRoute?: NavRoute;
  activeRoute?: NavRoute;
  onRouteChange: (route: NavRoute) => void;
  ollamaStatus?: OllamaStatusReport | null;
}

export const Navigation: React.FC<NavigationProps> = ({
  currentRoute,
  activeRoute,
  onRouteChange,
  ollamaStatus,
}) => {
  const selectedRoute = currentRoute || activeRoute || 'catalog';
  const navItems: { route: NavRoute; label: string; icon: React.ReactNode }[] = [
    { route: 'catalog', label: 'Explore Models', icon: <Compass size={16} /> },
    { route: 'compare', label: 'Compare Models', icon: <Scale size={16} /> },
    { route: 'evaluate', label: 'Evaluate Locally', icon: <PlayCircle size={16} /> },
    { route: 'history', label: 'Evaluation History', icon: <History size={16} /> },
    { route: 'settings', label: 'Settings & Daemon', icon: <Settings size={16} /> },
  ];

  const isOnline = ollamaStatus?.is_reachable && ollamaStatus?.status_label === 'online';
  const hasNoModels = ollamaStatus?.is_reachable && ollamaStatus?.status_label === 'no_models_installed';

  return (
    <header className="app-header">
      <div className="header-left">
        <div className="brand" onClick={() => onRouteChange('catalog')} role="button" tabIndex={0}>
          <span className="brand-icon">
            <Cpu size={18} />
          </span>
          <span className="brand-name">EvalForge<span className="brand-accent">20</span></span>
          <span className="brand-tag">LOCAL-FIRST</span>
        </div>

        <nav className="header-nav">
          {navItems.map((item) => (
            <button
              key={item.route}
              className={`nav-tab ${selectedRoute === item.route ? 'active' : ''}`}
              onClick={() => onRouteChange(item.route)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      <div className="header-right">
        {/* Ollama Daemon Status Pill */}
        <div
          className={`ollama-status-indicator ${
            isOnline ? 'online' : hasNoModels ? 'warning' : 'offline'
          }`}
          onClick={() => onRouteChange('settings')}
          title={ollamaStatus?.error_message || 'Click to view daemon diagnostics and settings'}
          role="button"
          tabIndex={0}
        >
          <span className="status-dot" />
          <span className="status-text">
            Ollama:{' '}
            {isOnline
              ? `${ollamaStatus?.models_count} Installed`
              : hasNoModels
              ? 'Online (No Models)'
              : 'Offline'}
          </span>
          <HardDrive size={13} style={{ marginLeft: '4px', opacity: 0.7 }} />
        </div>
      </div>
    </header>
  );
};
