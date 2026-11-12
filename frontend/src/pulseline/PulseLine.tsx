import React, { useState } from 'react';
import { WeekPoint } from '../data/types';

interface PulseLineProps {
  weeks: WeekPoint[];
  threshold?: number;
  height?: number;
}

export const PulseLine: React.FC<PulseLineProps> = ({
  weeks,
  threshold = 3.8,
  height = 140,
}) => {
  const [activeBeatIndex, setActiveBeatIndex] = useState<number | null>(null);

  if (!weeks || weeks.length === 0) {
    return null;
  }

  const viewBoxWidth = 1000;
  const viewBoxHeight = height;
  const baselineY = viewBoxHeight * 0.65;
  const stepX = viewBoxWidth / (weeks.length + 1);

  const beatCoords: { x: number; y: number; week: WeekPoint; isUnderThreshold: boolean }[] = [];

  const segments = weeks.map((week, idx) => {
    const centerX = stepX * (idx + 1);
    const prevCenterX = idx === 0 ? 0 : stepX * idx + stepX * 0.4;
    const nextCenterX = idx === weeks.length - 1 ? viewBoxWidth : stepX * (idx + 1) + stepX * 0.4;

    const normalizedRating = Math.max(1, Math.min(5, week.avgRating));
    const peakHeight = 15 + ((normalizedRating - 1) / 4) * 55;
    const peakY = baselineY - peakHeight;
    const dipY = baselineY + peakHeight * 0.28;
    const isUnderThreshold = week.avgRating < threshold;

    beatCoords.push({ x: centerX, y: peakY, week, isUnderThreshold });

    const p1x = centerX - 28;
    const p2x = centerX - 14;
    const dip1x = centerX - 6;
    const dip2x = centerX + 8;
    const p3x = centerX + 18;
    const p4x = centerX + 30;

    const pathData = `
      M ${prevCenterX} ${baselineY}
      L ${p1x} ${baselineY}
      Q ${p2x} ${baselineY - 6} ${p2x + 4} ${baselineY}
      L ${dip1x} ${baselineY + 8}
      L ${centerX} ${peakY}
      L ${dip2x} ${dipY}
      Q ${p3x} ${baselineY - 10} ${p3x + 6} ${baselineY}
      L ${p4x} ${baselineY}
      L ${nextCenterX} ${baselineY}
    `;

    return {
      index: idx,
      pathData,
      isUnderThreshold,
      week,
      centerX,
      peakY,
    };
  });

  return (
    <div className="relative w-full select-none" style={{ height: `${height}px` }}>
      <svg
        viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
        className="w-full h-full overflow-visible"
        aria-label="12-Week Customer Review Pulse ECG Graph"
        role="region"
      >
        <defs>
          {/* Luminous Neon Filters */}
          <filter id="ecgGlowTeal" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="ecgGlowAmber" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Area Gradients */}
          <linearGradient id="areaGradientTeal" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00D09C" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#00D09C" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Subtle grid lines */}
        <line
          x1="0"
          y1={baselineY}
          x2={viewBoxWidth}
          y2={baselineY}
          stroke="#1e293b"
          strokeWidth="1"
          strokeDasharray="4 4"
        />

        {/* ECG Segments with Neon Glow */}
        {segments.map((seg) => {
          const strokeColor = seg.isUnderThreshold ? '#F59E0B' : '#00D09C';
          const filterId = seg.isUnderThreshold ? 'url(#ecgGlowAmber)' : 'url(#ecgGlowTeal)';
          return (
            <g key={`seg-${seg.index}`}>
              <path
                d={seg.pathData}
                fill="none"
                stroke={strokeColor}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                filter={filterId}
                className="transition-colors duration-300"
              />
            </g>
          );
        })}

        {/* Interactive Beat Nodes */}
        {beatCoords.map((beat, idx) => {
          const isCurrent = beat.week.isCurrent;
          const isHovered = activeBeatIndex === idx;
          const fillColor = beat.isUnderThreshold ? '#F59E0B' : '#00D09C';

          return (
            <g
              key={`node-${idx}`}
              tabIndex={0}
              role="button"
              aria-label={`Week of ${beat.week.label}: Rating ${beat.week.avgRating.toFixed(1)} stars${
                beat.isUnderThreshold ? ' (below 3.8 threshold)' : ''
              }${isCurrent ? ' (Current Week)' : ''}`}
              onMouseEnter={() => setActiveBeatIndex(idx)}
              onMouseLeave={() => setActiveBeatIndex(null)}
              onFocus={() => setActiveBeatIndex(idx)}
              onBlur={() => setActiveBeatIndex(null)}
              className="cursor-pointer focus:outline-none"
            >
              {/* Outer pulsing ring for current beat */}
              {isCurrent && (
                <circle
                  cx={beat.x}
                  cy={beat.y}
                  r="14"
                  fill="none"
                  stroke={fillColor}
                  strokeWidth="2"
                  className="animate-pulse-glow"
                  opacity="0.65"
                />
              )}

              {/* Node core dot */}
              <circle
                cx={beat.x}
                cy={beat.y}
                r={isHovered ? 6 : isCurrent ? 5.5 : 4}
                fill={fillColor}
                stroke="#0b111e"
                strokeWidth="2"
                className="transition-all duration-200"
              />

              {/* Week date label below baseline */}
              <text
                x={beat.x}
                y={baselineY + 24}
                textAnchor="middle"
                fontSize="11"
                fontWeight={isCurrent ? '700' : '500'}
                fill={isCurrent ? '#f8fafc' : '#64748b'}
                className="select-none font-mono"
              >
                {beat.week.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Tooltip */}
      {activeBeatIndex !== null && (
        <div
          className="absolute z-20 pointer-events-none transform -translate-x-1/2 -translate-y-full bg-[#1b2a47] text-white text-xs py-1.5 px-3 rounded-lg border border-[#2a3d5d] shadow-drawer whitespace-nowrap transition-all duration-150"
          style={{
            left: `${((beatCoords[activeBeatIndex].x / viewBoxWidth) * 100).toFixed(1)}%`,
            top: `${Math.max(10, (beatCoords[activeBeatIndex].y / viewBoxHeight) * height - 8)}px`,
          }}
        >
          <div className="font-bold text-white font-display">
            Week of {beatCoords[activeBeatIndex].week.label}
          </div>
          <div className="flex items-center gap-1.5 text-text-secondary mt-0.5">
            <span>Avg:</span>
            <span
              className={`font-mono font-bold ${
                beatCoords[activeBeatIndex].isUnderThreshold ? 'text-friction-dark' : 'text-primary'
              }`}
            >
              {beatCoords[activeBeatIndex].week.avgRating.toFixed(1)}★
            </span>
            {beatCoords[activeBeatIndex].isUnderThreshold && (
              <span className="text-[10px] text-friction-dark bg-friction-tint px-1.5 py-0.5 rounded border border-friction-border font-mono">
                Under 3.8
              </span>
            )}
            {beatCoords[activeBeatIndex].week.isCurrent && (
              <span className="text-[10px] text-primary bg-primary-tint px-1.5 py-0.5 rounded border border-primary-border font-mono">
                Current
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
