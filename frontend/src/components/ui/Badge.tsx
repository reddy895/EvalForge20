import React from 'react';
import './Badge.css';

export type BadgeVariant = 'success' | 'error' | 'warning' | 'accent' | 'neutral';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  showDot?: boolean;
  className?: string;
  title?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  showDot = false,
  className = '',
  title,
}) => {
  return (
    <span className={`badge badge-${variant} ${className}`} title={title}>
      {showDot && <span className="badge-dot" aria-hidden="true" />}
      {children}
    </span>
  );
};

export interface StatusPillProps {
  status: 'completed' | 'running' | 'failed' | 'queued' | 'pending' | 'cancelled' | string;
}

export const StatusPill: React.FC<StatusPillProps> = ({ status }) => {
  const normalized = status.toLowerCase();

  switch (normalized) {
    case 'completed':
    case 'success':
      return (
        <Badge variant="success" showDot>
          Completed
        </Badge>
      );
    case 'running':
    case 'in_progress':
      return (
        <Badge variant="accent" showDot>
          Running
        </Badge>
      );
    case 'failed':
    case 'error':
      return (
        <Badge variant="error" showDot>
          Failed
        </Badge>
      );
    case 'queued':
    case 'pending':
      return (
        <Badge variant="warning" showDot>
          Queued
        </Badge>
      );
    case 'cancelled':
      return (
        <Badge variant="neutral" showDot>
          Cancelled
        </Badge>
      );
    default:
      return (
        <Badge variant="neutral" showDot>
          {status}
        </Badge>
      );
  }
};

export interface DeltaPillProps {
  delta: number;
  format?: (val: number) => string;
  higherIsBetter?: boolean;
}

export const DeltaPill: React.FC<DeltaPillProps> = ({
  delta,
  format = (val) => `${val >= 0 ? '+' : ''}${(val * 100).toFixed(1)}%`,
  higherIsBetter = true,
}) => {
  if (Math.abs(delta) < 0.0001) {
    return <span className="badge badge-delta-neutral">0.0%</span>;
  }

  const isPositive = delta > 0;
  const isImprovement = higherIsBetter ? isPositive : !isPositive;

  return (
    <span className={`badge ${isImprovement ? 'badge-delta-pos' : 'badge-delta-neg'}`}>
      {isImprovement ? '▲ ' : '▼ '}
      {format(delta)}
    </span>
  );
};
