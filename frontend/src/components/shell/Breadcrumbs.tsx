import React from 'react';
import { ChevronRight } from 'lucide-react';
import { type NavRoute } from '../../types/navigation';
import './Breadcrumbs.css';

export interface BreadcrumbStep {
  label: string;
  route?: NavRoute;
  onClick?: () => void;
}

interface BreadcrumbsProps {
  items: BreadcrumbStep[];
  onRouteChange: (route: NavRoute) => void;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items, onRouteChange }) => {
  if (!items || items.length === 0) return null;

  return (
    <nav className="breadcrumbs-nav" aria-label="Breadcrumb">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <span key={item.label} className="breadcrumb-item">
            {index > 0 && (
              <span className="breadcrumb-separator" aria-hidden="true">
                <ChevronRight size={12} />
              </span>
            )}
            {isLast ? (
              <span className="breadcrumb-current" aria-current="page">
                {item.label}
              </span>
            ) : (
              <button
                type="button"
                className="breadcrumb-link"
                onClick={() => {
                  if (item.onClick) {
                    item.onClick();
                  } else if (item.route) {
                    onRouteChange(item.route);
                  }
                }}
              >
                {item.label}
              </button>
            )}
          </span>
        );
      })}
    </nav>
  );
};
