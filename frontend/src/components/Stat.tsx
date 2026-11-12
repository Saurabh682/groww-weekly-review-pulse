import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Sentiment } from '../data/types';

interface StatProps {
  label: string;
  value: string | number;
  subtext?: string;
  trend?: number;
  trendLabel?: string;
  icon?: React.ReactNode;
  sentiment?: Sentiment;
  className?: string;
}

export const Stat: React.FC<StatProps> = ({
  label,
  value,
  subtext,
  trend,
  trendLabel,
  icon,
  className = '',
}) => {
  const isPositiveTrend = trend !== undefined && trend > 0;
  const isNegativeTrend = trend !== undefined && trend < 0;

  return (
    <div className={`flex flex-col ${className}`}>
      <div className="flex items-center justify-between text-text-secondary text-[11px] font-medium uppercase tracking-wider mb-1.5">
        <span>{label}</span>
        {icon && <span className="text-text-muted">{icon}</span>}
      </div>

      <div className="flex items-baseline gap-2.5">
        <span className="text-2xl font-bold font-display tracking-tight text-text-primary">
          {value}
        </span>

        {trend !== undefined && (
          <span
            className={`inline-flex items-center text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
              isPositiveTrend
                ? 'bg-primary-tint text-primary'
                : isNegativeTrend
                ? 'bg-critical-tint text-critical-dark'
                : 'text-text-muted'
            }`}
          >
            {isPositiveTrend ? (
              <TrendingUp className="w-3 h-3 mr-0.5" />
            ) : isNegativeTrend ? (
              <TrendingDown className="w-3 h-3 mr-0.5" />
            ) : null}
            {trend > 0 ? `+${trend.toFixed(1)}%` : `${trend.toFixed(1)}%`}
            {trendLabel && <span className="text-[10px] text-text-muted ml-1 font-normal">{trendLabel}</span>}
          </span>
        )}
      </div>

      {subtext && (
        <span className="text-xs text-text-muted mt-1 leading-tight">{subtext}</span>
      )}
    </div>
  );
};
