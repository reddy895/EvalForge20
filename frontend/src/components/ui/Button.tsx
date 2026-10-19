import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  loading = false,
  iconLeft,
  iconRight,
  disabled,
  className = '',
  ...props
}) => {
  const baseClasses =
    'inline-flex items-center justify-center font-medium rounded-full transition-all duration-150 select-none cursor-pointer disabled:opacity-45 disabled:cursor-not-allowed outline-none focus-visible:ring-2 focus-visible:ring-[#D9823B] focus-visible:ring-offset-2 focus-visible:ring-offset-[#191A18]';

  const sizeClasses = {
    sm: 'text-xs h-8 px-3.5 gap-1.5',
    md: 'text-sm h-10 px-5 gap-2',
    lg: 'text-base h-12 px-6 gap-2.5 font-semibold',
  }[size];

  const variantClasses = {
    primary:
      'bg-[#D9823B] text-[#191A18] hover:bg-[#E5914C] active:bg-[#C4722D] shadow-sm hover:shadow-[0_4px_16px_rgba(217,130,59,0.25)] hover:-translate-y-0.5 border border-[#D9823B]',
    secondary:
      'bg-[#242522] text-[#F5F0E7] hover:bg-[#333430] hover:border-[#54544D] active:bg-[#3C3D38] border border-[#41413B] shadow-sm hover:-translate-y-0.5',
    outline:
      'bg-transparent text-[#F5F0E7] hover:bg-white/5 hover:border-[#A6A49D] active:bg-white/10 border border-[#41413B] hover:-translate-y-0.5',
    ghost:
      'bg-transparent text-[#A6A49D] hover:text-[#F5F0E7] hover:bg-[#242522] border border-transparent',
    danger:
      'bg-red-500/10 text-[#D66D60] border border-red-500/30 hover:bg-red-500/20 active:bg-red-500/25',
  }[variant];

  return (
    <button
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        iconLeft && <span className="inline-flex shrink-0">{iconLeft}</span>
      )}
      {children && <span>{children}</span>}
      {!loading && iconRight && <span className="inline-flex shrink-0">{iconRight}</span>}
    </button>
  );
};
