import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverable?: boolean;
  clickable?: boolean;
  variant?: 'graphite' | 'ivory';
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  hoverable = false,
  clickable = false,
  variant = 'graphite',
  className = '',
  ...props
}) => {
  const baseClasses =
    variant === 'ivory'
      ? 'bg-[#FCFAF6] text-[#191A18] border border-[#DDD7CA]'
      : 'bg-[#242522] text-[#F5F0E7] border border-[#41413B]';

  const hoverClasses = hoverable
    ? variant === 'ivory'
      ? 'hover:border-[#D9823B] hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)] hover:-translate-y-1'
      : 'hover:border-[#D9823B]/60 hover:shadow-[0_8px_24px_rgba(0,0,0,0.4)] hover:-translate-y-1'
    : '';

  const cursorClass = clickable ? 'cursor-pointer' : '';

  return (
    <div
      className={`rounded-2xl p-6 transition-all duration-200 relative flex flex-col gap-4 ${baseClasses} ${hoverClasses} ${cursorClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`flex items-start justify-between gap-3 ${className}`}>{children}</div>;

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <h3 className={`text-base font-semibold tracking-tight text-inherit ${className}`}>{children}</h3>;

export const CardSubtitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <p className={`text-xs opacity-75 ${className}`}>{children}</p>;

export const CardBody: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`text-sm leading-relaxed opacity-90 ${className}`}>{children}</div>;

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`mt-auto pt-4 border-t border-current/10 flex items-center justify-between gap-3 ${className}`}>
    {children}
  </div>
);
