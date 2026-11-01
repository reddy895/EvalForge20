import React from 'react';
import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

/* BUTTON PRIMITIVE */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  className = '',
  disabled,
  ...props
}) => {
  const base =
    'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 disabled:opacity-50 disabled:pointer-events-none select-none';

  const variants = {
    primary: 'bg-[#2563EB] hover:bg-[#1D4ED8] text-white focus-visible:ring-[#2563EB]',
    secondary: 'bg-[#F1F5F9] hover:bg-[#E2E8F0] text-[#111827] focus-visible:ring-[#64748B]',
    danger: 'bg-[#DC2626] hover:bg-[#B91C1C] text-white focus-visible:ring-[#DC2626]',
    ghost: 'hover:bg-[#F1F5F9] text-[#64748B] hover:text-[#111827] focus-visible:ring-[#64748B]',
    outline: 'border border-[#E2E8F0] bg-white hover:bg-[#F8FAFC] text-[#111827] focus-visible:ring-[#2563EB]',
  };

  const sizes = {
    sm: 'text-xs px-2.5 py-1 gap-1.5',
    md: 'text-xs px-3.5 py-1.5 gap-2',
    lg: 'text-sm px-4 py-2 gap-2.5',
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
};

/* CARD PRIMITIVE */
export const Card: React.FC<{
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}> = ({ title, subtitle, children, className = '', action }) => (
  <div className={`bg-white border border-[#E2E8F0] rounded-lg shadow-sm ${className}`}>
    {(title || action) && (
      <div className="px-4 py-3 border-b border-[#E2E8F0] flex items-center justify-between">
        <div>
          {title && <h3 className="text-sm font-semibold text-[#111827]">{title}</h3>}
          {subtitle && <p className="text-xs text-[#64748B] mt-0.5">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
    )}
    <div className="p-4">{children}</div>
  </div>
);

/* BADGE PRIMITIVE */
export const Badge: React.FC<{
  children: React.ReactNode;
  variant?: 'neutral' | 'success' | 'warning' | 'error' | 'accent' | 'primary';
  className?: string;
}> = ({ children, variant = 'neutral', className = '' }) => {
  const styles: Record<string, string> = {
    neutral: 'bg-[#F1F5F9] text-[#64748B] border-[#E2E8F0]',
    success: 'bg-[#F0FDF4] text-[#16A34A] border-[#BBF7D0]',
    warning: 'bg-[#FFFBEB] text-[#D97706] border-[#FDE68A]',
    error: 'bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]',
    accent: 'bg-[#EFF6FF] text-[#2563EB] border-[#BFDBFE]',
    primary: 'bg-[#EFF6FF] text-[#2563EB] border-[#BFDBFE]',
  };

  return (
    <span
      className={`inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full border ${styles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};

/* ALERT PRIMITIVE */
export const Alert: React.FC<{
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
  className?: string;
}> = ({ type = 'info', title, children, className = '' }) => {
  const configs = {
    info: { bg: 'bg-[#EFF6FF]', border: 'border-[#BFDBFE]', text: 'text-[#1E40AF]', icon: Info },
    success: { bg: 'bg-[#F0FDF4]', border: 'border-[#BBF7D0]', text: 'text-[#166534]', icon: CheckCircle2 },
    warning: { bg: 'bg-[#FFFBEB]', border: 'border-[#FDE68A]', text: 'text-[#92400E]', icon: AlertCircle },
    error: { bg: 'bg-[#FEF2F2]', border: 'border-[#FECACA]', text: 'text-[#991B1B]', icon: AlertCircle },
  };

  const c = configs[type];
  const Icon = c.icon;

  return (
    <div className={`p-3 rounded-md border ${c.bg} ${c.border} ${c.text} flex gap-2.5 ${className}`}>
      <Icon className="w-4 h-4 shrink-0 mt-0.5" />
      <div className="text-xs">
        {title && <div className="font-semibold mb-0.5">{title}</div>}
        <div>{children}</div>
      </div>
    </div>
  );
};

/* EMPTY STATE PRIMITIVE */
export const EmptyState: React.FC<{
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  action?: React.ReactNode;
}> = ({ icon: Icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center p-8 text-center bg-white border border-[#E2E8F0] rounded-lg">
    <div className="w-10 h-10 rounded-full bg-[#F1F5F9] flex items-center justify-center text-[#64748B] mb-3">
      <Icon className="w-5 h-5" />
    </div>
    <h4 className="text-sm font-semibold text-[#111827]">{title}</h4>
    <p className="text-xs text-[#64748B] max-w-sm mt-1 mb-4">{description}</p>
    {action}
  </div>
);
