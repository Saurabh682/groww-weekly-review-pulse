import React from 'react';
import { CheckCircle2, AlertTriangle, X } from 'lucide-react';

interface ToastProps {
  message: string;
  type?: 'success' | 'warning' | 'info';
  onClose?: () => void;
}

export const Toast: React.FC<ToastProps> = ({
  message,
  type = 'success',
  onClose,
}) => {
  const typeStyles = {
    success: 'bg-[#1b2a47] text-text-primary border-primary/40 shadow-glow-teal-sm',
    warning: 'bg-friction-tint text-friction-dark border-friction-border shadow-glow-amber',
    info: 'bg-surface-elevated text-text-primary border-border-subtle shadow-card',
  };

  const icons = {
    success: <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />,
    warning: <AlertTriangle className="w-4 h-4 text-friction shrink-0" />,
    info: null,
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-drawer border text-xs font-semibold backdrop-blur-lg animate-fade-in ${typeStyles[type]}`}
    >
      {icons[type]}
      <span>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-2 text-text-muted hover:text-white transition-colors"
          aria-label="Dismiss toast"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
