import React, { useEffect } from 'react';
import { X, Terminal, Plus } from 'lucide-react';
import { NAVIGATION_STRUCTURE, type NavRoute } from '../../types/navigation';
import './MobileDrawer.css';

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  currentRoute: NavRoute;
  onRouteChange: (route: NavRoute) => void;
}

export const MobileDrawer: React.FC<MobileDrawerProps> = ({
  isOpen,
  onClose,
  currentRoute,
  onRouteChange,
}) => {
  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleNavClick = (route: NavRoute) => {
    onRouteChange(route);
    onClose();
  };

  return (
    <>
      <div
        className={`mobile-drawer-backdrop ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        className={`mobile-drawer ${isOpen ? 'open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation Drawer"
      >
        <div className="mobile-drawer-header">
          <div className="sidebar-brand">
            <Terminal size={16} className="text-accent" />
            <span>EvalForge20</span>
          </div>
          <button
            type="button"
            className="mobile-drawer-close-btn"
            onClick={onClose}
            aria-label="Close navigation drawer"
          >
            <X size={16} />
          </button>
        </div>

        <div className="sidebar-cta-wrap">
          <button
            type="button"
            className="sidebar-cta-btn"
            onClick={() => handleNavClick('new-eval')}
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
                  const isActive =
                    currentRoute === item.id ||
                    (item.id === 'runs' && currentRoute === 'run-detail');

                  return (
                    <li key={item.id}>
                      <button
                        type="button"
                        className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                        onClick={() => handleNavClick(item.id)}
                      >
                        <div className="sidebar-nav-link-content">
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
      </div>
    </>
  );
};
