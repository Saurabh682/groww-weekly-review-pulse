import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'rect' | 'circle' | 'text';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  variant = 'rect',
}) => {
  const variantStyles = {
    rect: 'rounded-lg',
    circle: 'rounded-full',
    text: 'rounded h-4',
  };

  return (
    <div
      className={`animate-pulse bg-surface-elevated/60 border border-border-glass ${variantStyles[variant]} ${className}`}
      aria-hidden="true"
    />
  );
};
