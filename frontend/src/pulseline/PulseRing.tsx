import React from 'react';
import { Theme } from '../data/types';
import { Activity } from 'lucide-react';

interface PulseRingProps {
  themes: Theme[];
  selectedThemeId?: string;
  onSelectTheme?: (theme: Theme) => void;
  className?: string;
}

export const PulseRing: React.FC<PulseRingProps> = ({
  themes,
  selectedThemeId,
  onSelectTheme,
  className = '',
}) => {
  if (!themes || themes.length === 0) return null;

  const width = 360;
  const height = 360;
  const centerX = width / 2;
  const centerY = height / 2;
  const orbitRadius = 120;

  const colorMap = {
    positive: { stroke: '#00D09C', fill: 'rgba(0, 208, 156, 0.18)', text: '#00D09C' },
    friction: { stroke: '#F59E0B', fill: 'rgba(245, 158, 11, 0.18)', text: '#FBBF24' },
    critical: { stroke: '#F43F5E', fill: 'rgba(244, 63, 94, 0.18)', text: '#FB7185' },
  };

  return (
    <div className={`relative flex items-center justify-center select-none ${className}`}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-[320px] h-[320px] md:w-[360px] md:h-[360px] overflow-visible"
        aria-label="Theme Neural Cluster Radial Pulse Map"
      >
        <defs>
          <filter id="ringGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Outer Orbit Guide Line */}
        <circle
          cx={centerX}
          cy={centerY}
          r={orbitRadius}
          fill="none"
          stroke="#1e293b"
          strokeWidth="1.5"
          strokeDasharray="4 4"
        />

        {/* Orbit Connectors to Center */}
        {themes.map((theme, idx) => {
          const angle = (idx * (2 * Math.PI)) / themes.length - Math.PI / 2;
          const nodeX = centerX + orbitRadius * Math.cos(angle);
          const nodeY = centerY + orbitRadius * Math.sin(angle);
          const colors = colorMap[theme.sentiment] || colorMap.friction;
          const isSelected = selectedThemeId === theme.id;

          return (
            <line
              key={`conn-${theme.id}`}
              x1={centerX}
              y1={centerY}
              x2={nodeX}
              y2={nodeY}
              stroke={isSelected ? colors.stroke : '#1e293b'}
              strokeWidth={isSelected ? '2' : '1'}
              strokeDasharray={isSelected ? 'none' : '2 2'}
              className="transition-colors duration-200"
            />
          );
        })}

        {/* Central Pulse Core */}
        <g
          transform={`translate(${centerX}, ${centerY})`}
          className="cursor-default"
        >
          <circle
            r="28"
            fill="#0e1726"
            stroke="#00D09C"
            strokeWidth="2"
            className="shadow-glow-teal-sm"
          />
          <circle
            r="36"
            fill="none"
            stroke="#00D09C"
            strokeWidth="1.5"
            opacity="0.4"
            className="animate-pulse-glow"
          />
        </g>

        {/* Orbit Theme Nodes */}
        {themes.map((theme, idx) => {
          const angle = (idx * (2 * Math.PI)) / themes.length - Math.PI / 2;
          const nodeX = centerX + orbitRadius * Math.cos(angle);
          const nodeY = centerY + orbitRadius * Math.sin(angle);

          const nodeRadius = Math.max(20, Math.min(36, Math.round(18 + (theme.sharePct / 40) * 16)));
          const colors = colorMap[theme.sentiment] || colorMap.friction;
          const isSelected = selectedThemeId === theme.id;

          return (
            <g
              key={theme.id}
              tabIndex={0}
              role="button"
              aria-label={`Theme ${theme.rank}: ${theme.label}, ${theme.sharePct.toFixed(1)}% share`}
              onClick={() => onSelectTheme && onSelectTheme(theme)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectTheme && onSelectTheme(theme);
                }
              }}
              className="cursor-pointer group focus:outline-none"
            >
              {isSelected && (
                <circle
                  cx={nodeX}
                  cy={nodeY}
                  r={nodeRadius + 6}
                  fill="none"
                  stroke={colors.stroke}
                  strokeWidth="2"
                  className="animate-pulse-glow"
                />
              )}

              {/* Theme Bubble */}
              <circle
                cx={nodeX}
                cy={nodeY}
                r={nodeRadius}
                fill={colors.fill}
                stroke={colors.stroke}
                strokeWidth={isSelected ? '3' : '2'}
                filter="url(#ringGlow)"
                className="transition-all duration-200 group-hover:scale-105"
              />

              {/* Text Inside Node */}
              <text
                x={nodeX}
                y={nodeY - 2}
                textAnchor="middle"
                fontSize="12"
                fontWeight="700"
                fill={colors.text}
                className="pointer-events-none select-none font-display"
              >
                #{theme.rank}
              </text>
              <text
                x={nodeX}
                y={nodeY + 11}
                textAnchor="middle"
                fontSize="9"
                fontWeight="700"
                fill={colors.text}
                className="pointer-events-none select-none font-mono"
              >
                {theme.sharePct.toFixed(0)}%
              </text>
            </g>
          );
        })}
      </svg>

      {/* Center Icon Overlay */}
      <div className="absolute pointer-events-none text-primary flex items-center justify-center">
        <Activity className="w-6 h-6 animate-heartbeat text-primary" />
      </div>
    </div>
  );
};
