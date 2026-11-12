import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'teal' | 'amber' | 'coral' | 'blue' | 'gray' | 'dark';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'teal',
  className = '',
}) => {
  const variantStyles = {
    teal: 'bg-primary-tint text-primary border border-primary-border',
    amber: 'bg-friction-tint text-friction-dark border border-friction-border',
    coral: 'bg-critical-tint text-critical-dark border border-critical-border',
    blue: 'bg-blue-tint text-blue border border-blue-border',
    gray: 'bg-surface-elevated/80 text-text-secondary border border-border-glass',
    dark: 'bg-surface-highest text-text-primary border border-border-subtle',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold tracking-wide leading-none ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
