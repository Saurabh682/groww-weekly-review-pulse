import React from 'react';
import { Sentiment } from '../data/types';

interface ChipProps {
  label: string;
  variant?: Sentiment | 'neutral' | 'outline' | 'failure' | 'blue';
  icon?: React.ReactNode;
  size?: 'sm' | 'md';
  className?: string;
}

export const Chip: React.FC<ChipProps> = ({
  label,
  variant = 'neutral',
  icon,
  size = 'md',
  className = '',
}) => {
  const variantStyles = {
    positive: 'bg-primary-tint text-primary border border-primary-border shadow-glow-teal-sm',
    friction: 'bg-friction-tint text-friction-dark border border-friction-border shadow-glow-amber',
    critical: 'bg-critical-tint text-critical-dark border border-critical-border shadow-glow-coral',
    failure: 'bg-failure-tint text-failure-dark border border-failure-border',
    blue: 'bg-blue-tint text-blue border border-blue-border',
    neutral: 'bg-surface-elevated/70 text-text-secondary border border-border-subtle',
    outline: 'bg-transparent text-text-secondary border border-border-subtle',
  };

  const sizeStyles = {
    sm: 'text-[11px] py-0.5 px-2.5 gap-1 font-mono',
    md: 'text-xs py-1 px-3 gap-1.5 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center rounded-chip transition-all duration-150 ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{label}</span>
    </span>
  );
};
