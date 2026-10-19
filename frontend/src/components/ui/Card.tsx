import React from 'react';
import './Card.css';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
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
  const classes = [
    'ef-card',
    hoverable && 'ef-card-hoverable',
    clickable && 'ef-card-clickable',
    variant === 'ivory' && 'ef-card-ivory',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`ef-card-header ${className}`}>{children}</div>;

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <h3 className={`ef-card-title ${className}`}>{children}</h3>;

export const CardSubtitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <p className={`ef-card-subtitle ${className}`}>{children}</p>;

export const CardBody: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`ef-card-body ${className}`}>{children}</div>;

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`ef-card-footer ${className}`}>{children}</div>;
