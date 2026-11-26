import React from 'react';
import { Sentiment } from '../data/types';

type CardVariant = 'default' | 'elevated' | 'interactive';
type CardPadding = 'none' | 'tight' | 'normal' | 'roomy';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: CardVariant;
  padding?: CardPadding;
  tone?: Sentiment;
}

const VARIANT_STYLES: Record<CardVariant, string> = {
  default: 'bg-surface/80 backdrop-blur-md border border-border-glass shadow-card',
  elevated: 'bg-surface-elevated/85 backdrop-blur-lg border border-border shadow-card',
  interactive:
    'bg-surface/80 backdrop-blur-md border border-border-glass shadow-card hover:bg-surface-elevated/90 hover:border-primary/40 hover:shadow-hover transition-all duration-200 cursor-pointer',
};

const PADDING_STYLES: Record<CardPadding, string> = {
  none: 'p-0',
  tight: 'p-4',
  normal: 'p-5',
  roomy: 'p-6',
};

const TONE_STYLES: Record<Sentiment, string> = {
  positive: '!border-primary/30 hover:!border-primary/60',
  friction: '!border-friction/30 hover:!border-friction/60',
  critical: '!border-critical/30 hover:!border-critical/60',
};

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'default',
  padding = 'normal',
  tone,
  ...props
}) => (
  <div
    className={`rounded-card ${PADDING_STYLES[padding]} ${VARIANT_STYLES[variant]} ${tone ? TONE_STYLES[tone] : ''} ${className}`}
    {...props}
  >
    {children}
  </div>
);
