import React from 'react';
import { Sentiment } from '../data/types';
import { CSS_COLOUR } from '../styles/cssColours';

interface PulseNodeProps {
  sharePct: number;
  sentiment: Sentiment;
  rank?: number;
  showConnector?: boolean;
  className?: string;
}

export const PulseNode: React.FC<PulseNodeProps> = ({
  sharePct,
  sentiment,
  rank,
  showConnector = false,
  className = '',
}) => {
  const diameter = Math.max(14, Math.min(32, Math.round(12 + (sharePct / 40) * 18)));

  const colorMap = {
    positive: {
      bg: CSS_COLOUR.primaryTint,
      border: CSS_COLOUR.primary,
      text: CSS_COLOUR.primary,
    },
    friction: {
      bg: CSS_COLOUR.frictionTint,
      border: CSS_COLOUR.friction,
      text: CSS_COLOUR.frictionDark,
    },
    critical: {
      bg: CSS_COLOUR.criticalTint,
      border: CSS_COLOUR.critical,
      text: CSS_COLOUR.criticalDark,
    },
  };

  const colors = colorMap[sentiment] || colorMap.friction;

  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      {showConnector && (
        <div
          className="absolute -top-6 w-[2px] h-6 bg-border"
          aria-hidden="true"
        />
      )}
      <div
        style={{
          width: `${diameter}px`,
          height: `${diameter}px`,
          backgroundColor: colors.bg,
          borderColor: colors.border,
        }}
        className="rounded-full border-2 flex items-center justify-center font-bold text-3xs font-mono shadow-sm transition-transform duration-200 hover:scale-110"
        title={`Theme share: ${sharePct.toFixed(1)}%`}
      >
        {diameter >= 22 && rank && (
          <span style={{ color: colors.text }}>#{rank}</span>
        )}
      </div>
    </div>
  );
};
