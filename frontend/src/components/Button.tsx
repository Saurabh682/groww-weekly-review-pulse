import React from 'react';
import { Loader2 } from 'lucide-react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

const VARIANT_STYLES: Record<ButtonVariant, string> = {
  primary: 'bg-primary text-primary-on font-bold hover:brightness-110 hover:shadow-glow-teal active:scale-[0.99] transition-all shadow-glow-teal-sm disabled:opacity-40 disabled:cursor-not-allowed',
  secondary: 'bg-surface-elevated/70 text-text-primary border border-border-subtle hover:bg-surface-elevated hover:border-primary/40 active:bg-surface-highest transition-all shadow-subtle disabled:opacity-40 disabled:cursor-not-allowed',
  ghost: 'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-elevated/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed',
  danger: 'bg-critical/90 text-white hover:bg-critical hover:shadow-glow-coral active:scale-[0.99] transition-all shadow-subtle disabled:opacity-40 disabled:cursor-not-allowed',
};

const SIZE_STYLES: Record<ButtonSize, string> = {
  sm: 'text-xs px-3 py-1.5 rounded-lg gap-1.5',
  md: 'text-sm px-4 py-2 rounded-lg gap-2',
  lg: 'text-base px-5 py-2.5 rounded-xl gap-2.5',
};

const buttonClasses = (variant: ButtonVariant, size: ButtonSize, className: string) =>
  `inline-flex items-center justify-center font-medium transition-all duration-150 select-none ${SIZE_STYLES[size]} ${VARIANT_STYLES[variant]} ${className}`;

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
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
  type = 'button',
  ...props
}) => {
  return (
    <button className={buttonClasses(variant, size, className)} disabled={disabled || loading} type={type} {...props}>
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};

interface ButtonLinkProps extends Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, 'href' | 'target' | 'rel'> {
  href: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
}

export const ExternalButtonLink: React.FC<ButtonLinkProps> = ({
  children,
  href,
  variant = 'secondary',
  size = 'sm',
  icon,
  className = '',
  ...props
}) => (
  <a href={href} target="_blank" rel="noreferrer" className={buttonClasses(variant, size, className)} {...props}>
    {icon && <span className="flex-shrink-0">{icon}</span>}
    {children}
  </a>
);
