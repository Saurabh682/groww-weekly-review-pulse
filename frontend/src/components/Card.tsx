import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'interactive';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'default',
  ...props
}) => {
  const variantStyles = {
    default: 'bg-surface/80 backdrop-blur-md border border-border-glass shadow-card',
    elevated: 'bg-surface-elevated/85 backdrop-blur-lg border border-border shadow-card',
    interactive: 'bg-surface/80 backdrop-blur-md border border-border-glass shadow-card hover:bg-surface-elevated/90 hover:border-primary/40 hover:shadow-hover transition-all duration-200 cursor-pointer',
  };

  return (
    <div
      className={`rounded-card p-5 ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
