import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
  className = '',
}) => {
  return (
    <div
      role="alert"
      className={`p-5 rounded-card bg-failure-tint border border-failure-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${className}`}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-failure/20 text-failure flex-shrink-0 mt-0.5 border border-failure/40">
          <AlertCircle className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold font-display text-failure-dark">{title}</h4>
          <p className="text-xs text-failure-dark/80 mt-0.5 max-w-xl leading-relaxed">{message}</p>
        </div>
      </div>

      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          icon={<RefreshCw className="w-3.5 h-3.5" />}
          className="border-failure/40 hover:bg-failure-tint text-failure-dark"
        >
          Retry
        </Button>
      )}
    </div>
  );
};
