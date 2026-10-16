import React from 'react';
import {
  LayoutDashboard,
  PlayCircle,
  GitCompare,
  Database,
  Cpu,
  CheckSquare,
  FileText,
  Layers,
  Bot,
  Settings,
  Plus,
  Terminal,
} from 'lucide-react';
import { NAVIGATION_STRUCTURE, type NavRoute } from '../../types/navigation';
import './Sidebar.css';

interface SidebarProps {
  currentRoute: NavRoute;
  onRouteChange: (route: NavRoute) => void;
  systemReady?: boolean;
}

const ROUTE_ICONS: Record<NavRoute, React.ComponentType<{ className?: string }>> = {
  overview: LayoutDashboard,
  runs: PlayCircle,
  'run-detail': PlayCircle,
  'new-eval': Plus,
  compare: GitCompare,
  datasets: Database,
  providers: Cpu,
  evaluators: CheckSquare,
  reports: FileText,
  rag: Layers,
  agents: Bot,
  settings: Settings,
};

export const Sidebar: React.FC<SidebarProps> = ({
  currentRoute,
  onRouteChange,
  systemReady = true,
}) => {
  return (
    <aside className="sidebar" aria-label="Main Navigation">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <Terminal className="sidebar-nav-icon text-accent" />
          <span>EvalForge20</span>
        </div>
        <span className="sidebar-brand-badge">v0.1.0</span>
      </div>

      <div className="sidebar-cta-wrap">
        <button
          type="button"
          className="sidebar-cta-btn"
          onClick={() => onRouteChange('new-eval')}
          id="btn-sidebar-new-eval"
        >
          <Plus size={14} />
          <span>New Evaluation</span>
        </button>
      </div>

      <div className="sidebar-scroll">
        {NAVIGATION_STRUCTURE.map((section) => (
          <div key={section.title} className="sidebar-section">
            <div className="sidebar-section-title">{section.title}</div>
            <ul className="sidebar-nav-list" role="list">
              {section.items.map((item) => {
                const IconComponent = ROUTE_ICONS[item.id] || LayoutDashboard;
                const isActive =
                  currentRoute === item.id ||
                  (item.id === 'runs' && currentRoute === 'run-detail');

                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                      onClick={() => onRouteChange(item.id)}
                      id={`nav-item-${item.id}`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <div className="sidebar-nav-link-content">
                        <IconComponent className="sidebar-nav-icon" />
                        <span>{item.label}</span>
                      </div>
                      {item.badge && (
                        <span className="sidebar-nav-badge">{item.badge}</span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-footer-status">
          <span
            className="status-indicator-dot"
            style={{
              backgroundColor: systemReady ? 'var(--status-success)' : 'var(--status-error)',
            }}
          />
          <span>{systemReady ? 'Local Engine Ready' : 'Backend Disconnected'}</span>
        </div>
        <span className="font-mono">SQLite: OK</span>
      </div>
    </aside>
  );
};
