import React from 'react';
import './MetricCard.css';

export interface MetricCardProps {
  title: string;
  value: string | number | null | undefined;
  unit?: string;
  footer?: string;
  icon?: React.ReactNode;
  isLoading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  footer,
  icon,
  isLoading = false,
}) => {
  return (
    <div className="metric-card">
      <div className="metric-card-header">
        <span className="metric-card-title">{title}</span>
        {icon && <span className="metric-card-icon">{icon}</span>}
      </div>

      <div className="metric-card-body">
        {isLoading ? (
          <div className="metric-card-skeleton" />
        ) : (
          <>
            <span className="metric-card-value">{value !== null && value !== undefined ? value : '—'}</span>
            {unit && <span className="metric-card-unit">{unit}</span>}
          </>
        )}
      </div>

      {footer && <div className="metric-card-footer">{footer}</div>}
    </div>
  );
};
