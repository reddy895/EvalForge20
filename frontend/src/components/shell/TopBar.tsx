import React from 'react';
import { Menu, Activity, RefreshCw } from 'lucide-react';
import './TopBar.css';

interface TopBarProps {
  currentWorkspace: string;
  onWorkspaceChange: (workspace: string) => void;
  onToggleMobileMenu: () => void;
  ollamaConnected?: boolean;
  onRefreshStatus?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  currentWorkspace,
  onWorkspaceChange,
  onToggleMobileMenu,
  ollamaConnected = false,
  onRefreshStatus,
}) => {
  return (
    <header className="topbar" role="banner">
      <div className="topbar-left">
        <button
          type="button"
          className="topbar-mobile-menu-btn"
          onClick={onToggleMobileMenu}
          aria-label="Open mobile navigation menu"
          id="btn-mobile-nav-toggle"
        >
          <Menu size={16} />
        </button>

        <div className="workspace-selector-wrap">
          <span className="workspace-label">Workspace:</span>
          <select
            className="workspace-select"
            value={currentWorkspace}
            onChange={(e) => onWorkspaceChange(e.target.value)}
            id="select-workspace"
            aria-label="Select active workspace"
          >
            <option value="reddy895/EvalForge20">reddy895/EvalForge20</option>
            <option value="local/research-benchmarks">local/research-benchmarks</option>
            <option value="ci/regression-suite">ci/regression-suite</option>
          </select>
        </div>
      </div>

      <div className="topbar-right">
        <div
          className={`topbar-badge ${ollamaConnected ? 'healthy' : 'unhealthy'}`}
          title={
            ollamaConnected
              ? 'Local Ollama service running on localhost:11434'
              : 'Ollama daemon unreachable or not responding'
          }
        >
          <span className="topbar-badge-dot" />
          <span className="topbar-badge-text">
            Ollama: {ollamaConnected ? '11434 (Active)' : 'Offline'}
          </span>
        </div>

        {onRefreshStatus && (
          <button
            type="button"
            className="topbar-quick-action"
            onClick={onRefreshStatus}
            id="btn-sync-status"
            title="Refresh local engine and provider daemon status"
            aria-label="Refresh system status"
          >
            <RefreshCw size={13} />
            <span className="hide-on-mobile">Sync Status</span>
          </button>
        )}

        <div className="topbar-badge">
          <Activity size={12} />
          <span className="topbar-badge-text font-mono">SQLite: Local</span>
        </div>
      </div>
    </header>
  );
};
