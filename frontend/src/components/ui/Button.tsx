import React from 'react';
import './Button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  iconOnly?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'secondary',
      size = 'md',
      loading = false,
      iconLeft,
      iconRight,
      iconOnly = false,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={`btn btn-${variant} btn-${size} ${iconOnly ? 'btn-icon-only' : ''} ${
          loading ? 'loading' : ''
        } ${className}`}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <span className="btn-spinner" aria-hidden="true" />
        ) : (
          <>
            {iconLeft && <span className="btn-icon">{iconLeft}</span>}
            {children}
            {iconRight && <span className="btn-icon">{iconRight}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
