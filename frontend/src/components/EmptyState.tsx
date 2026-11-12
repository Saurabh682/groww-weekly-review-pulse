import React from 'react';
import { Inbox } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  actionLabel,
  onAction,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-12 text-center bg-surface/60 border border-border-subtle border-dashed rounded-card ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-surface-elevated flex items-center justify-center text-text-muted mb-4 border border-border">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h3 className="text-base font-bold font-display text-text-primary mb-1">{title}</h3>
      <p className="text-xs text-text-secondary max-w-md mb-6 leading-relaxed">{description}</p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
