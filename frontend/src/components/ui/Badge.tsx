import React from 'react';
import './Badge.css';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral' | 'accent' | 'danger' | 'task';
  className?: string;
  title?: string;
  showDot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className = '',
  title,
  showDot = false,
}) => {
  const normalizedVariant = variant === 'danger' ? 'error' : variant;

  return (
    <span
      className={`badge badge-${normalizedVariant} ${className}`}
      title={title}
    >
      {showDot && <span className="badge-dot" />}
      {children}
    </span>
  );
};

export const StatusPill = Badge;
