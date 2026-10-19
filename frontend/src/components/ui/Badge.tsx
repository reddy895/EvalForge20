import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?:
    | 'success'
    | 'error'
    | 'warning'
    | 'info'
    | 'neutral'
    | 'accent'
    | 'task'
    | 'installed'
    | 'outline'
    | 'demo';
  size?: 'sm' | 'md';
  showDot?: boolean;
  className?: string;
  title?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  showDot = false,
  className = '',
  title,
}) => {
  const sizeClasses = size === 'sm' ? 'text-[11px] px-2.5 py-0.5' : 'text-xs px-3 py-1';

  const variantClasses = {
    success: 'bg-[#68B587]/15 text-[#68B587] border-[#68B587]/30',
    error: 'bg-[#D66D60]/15 text-[#D66D60] border-[#D66D60]/30',
    warning: 'bg-[#D99D4B]/15 text-[#D99D4B] border-[#D99D4B]/30',
    info: 'bg-[#A6A49D]/15 text-[#A6A49D] border-[#A6A49D]/30',
    neutral: 'bg-[#242522] text-[#A6A49D] border-[#41413B]',
    accent: 'bg-[#D9823B]/15 text-[#D9823B] border-[#D9823B]/35',
    task: 'bg-[#D9823B]/10 text-[#D9823B] border-[#D9823B]/25 capitalize',
    installed: 'bg-[#68B587]/15 text-[#68B587] border-[#68B587]/30 font-mono',
    outline: 'bg-transparent text-[#A6A49D] border-[#41413B] font-mono',
    demo: 'bg-[#D9823B]/15 text-[#D9823B] border-[#D9823B]/35 font-mono',
  }[variant];

  const dotColor = {
    success: 'bg-[#68B587]',
    error: 'bg-[#D66D60]',
    warning: 'bg-[#D99D4B]',
    info: 'bg-[#A6A49D]',
    neutral: 'bg-[#A6A49D]',
    accent: 'bg-[#D9823B]',
    task: 'bg-[#D9823B]',
    installed: 'bg-[#68B587]',
    outline: 'bg-[#A6A49D]',
    demo: 'bg-[#D9823B]',
  }[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border whitespace-nowrap leading-none ${sizeClasses} ${variantClasses} ${className}`}
      title={title}
    >
      {showDot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor}`} />}
      {children}
    </span>
  );
};
