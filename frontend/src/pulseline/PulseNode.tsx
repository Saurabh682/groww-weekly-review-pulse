import React from 'react';
import { Sentiment } from '../data/types';

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
      bg: 'rgba(0, 208, 156, 0.15)',
      border: '#00D09C',
      text: '#00D09C',
    },
    friction: {
      bg: 'rgba(245, 158, 11, 0.15)',
      border: '#F59E0B',
      text: '#FBBF24',
    },
    critical: {
      bg: 'rgba(244, 63, 94, 0.15)',
      border: '#F43F5E',
      text: '#FB7185',
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
        className="rounded-full border-2 flex items-center justify-center font-bold text-[10px] font-mono shadow-sm transition-transform duration-200 hover:scale-110"
        title={`Theme share: ${sharePct.toFixed(1)}%`}
      >
        {diameter >= 22 && rank && (
          <span style={{ color: colors.text }}>#{rank}</span>
        )}
      </div>
    </div>
  );
};
