import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from './Button';
import { HeadingLevel } from './headingLevel';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  compact?: boolean;
  headingLevel: HeadingLevel;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  actionLabel,
  onAction,
  compact = false,
  headingLevel,
  className = '',
}) => {
  const Heading = `h${headingLevel}` as const;
  return (
    <div
      className={`flex flex-col items-center justify-center ${compact ? 'p-6' : 'p-12'} text-center bg-surface/60 border border-border-subtle border-dashed rounded-card ${className}`}
    >
      {!compact && (
        <div className="w-12 h-12 rounded-full bg-surface-elevated flex items-center justify-center text-text-muted mb-4 border border-border">
          {icon || <Inbox className="w-6 h-6" />}
        </div>
      )}
      <Heading className="text-base font-bold font-display text-text-primary mb-1">{title}</Heading>
      <p className={`text-xs text-text-secondary max-w-md leading-relaxed ${actionLabel && onAction ? 'mb-6' : ''}`}>{description}</p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
