import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral' | 'accent' | 'danger';
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
      className={`badge badge-${normalizedVariant} ${className} inline-flex items-center gap-1.5`}
      title={title}
    >
      {showDot && (
        <span
          className={`badge-dot w-1.5 h-1.5 rounded-full ${
            normalizedVariant === 'success'
              ? 'bg-[#8BAF78]'
              : normalizedVariant === 'error'
              ? 'bg-[#D97767]'
              : normalizedVariant === 'warning'
              ? 'bg-[#DE9E4E]'
              : normalizedVariant === 'accent'
              ? 'bg-[#E58B45]'
              : 'bg-[#A5A59A]'
          }`}
        />
      )}
      {children}
    </span>
  );
};

export const StatusPill = Badge;
