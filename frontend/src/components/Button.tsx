import React from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  loading = false,
  disabled,
  className = '',
  ...props
}) => {
  const variantStyles = {
    primary: 'bg-primary text-[#0b111e] font-bold hover:brightness-110 hover:shadow-glow-teal active:scale-[0.99] transition-all shadow-glow-teal-sm disabled:opacity-40 disabled:cursor-not-allowed',
    secondary: 'bg-surface-elevated/70 text-text-primary border border-border-subtle hover:bg-surface-elevated hover:border-primary/40 active:bg-surface-highest transition-all shadow-subtle disabled:opacity-40 disabled:cursor-not-allowed',
    ghost: 'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-elevated/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed',
    danger: 'bg-critical/90 text-white hover:bg-critical hover:shadow-glow-coral active:scale-[0.99] transition-all shadow-subtle disabled:opacity-40 disabled:cursor-not-allowed',
  };

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 rounded-lg gap-1.5',
    md: 'text-sm px-4 py-2 rounded-lg gap-2',
    lg: 'text-base px-5 py-2.5 rounded-xl gap-2.5',
  };

  return (
    <button
      className={`inline-flex items-center justify-center font-medium transition-all duration-150 select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};
