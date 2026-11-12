import React, { useState } from 'react';

interface VolumePoint {
  week: string;
  count: number;
}

interface PulseWaveMiniProps {
  data: VolumePoint[];
  height?: number;
}

export const PulseWaveMini: React.FC<PulseWaveMiniProps> = ({
  data,
  height = 64,
}) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) return null;

  const width = 600;
  const maxCount = Math.max(...data.map((d) => d.count), 100);
  const baselineY = height * 0.8;
  const stepX = width / (data.length + 1);

  let pathD = `M 0 ${baselineY} `;
  const markers: { x: number; y: number; week: string; count: number; isMissing: boolean }[] = [];

  data.forEach((point, idx) => {
    const x = stepX * (idx + 1);
    const isMissing = point.count === 0;
    const peakHeight = isMissing ? 0 : (point.count / maxCount) * (height * 0.65);
    const y = baselineY - peakHeight;

    markers.push({ x, y: isMissing ? baselineY : y, week: point.week, count: point.count, isMissing });

    if (isMissing) {
      pathD += `L ${x} ${baselineY} `;
    } else {
      pathD += `L ${x - 8} ${baselineY} L ${x} ${y} L ${x + 8} ${baselineY} `;
    }
  });

  pathD += `L ${width} ${baselineY}`;

  return (
    <div className="relative w-full" style={{ height: `${height}px` }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full overflow-visible"
        aria-label="Weekly review volume waveform"
      >
        <defs>
          <filter id="waveGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Baseline */}
        <line
          x1="0"
          y1={baselineY}
          x2={width}
          y2={baselineY}
          stroke="#1e293b"
          strokeWidth="1"
          strokeDasharray="2 2"
        />

        {/* Volume waveform path */}
        <path
          d={pathD}
          fill="none"
          stroke="#00D09C"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#waveGlow)"
        />

        {/* Data points & missing week markers */}
        {markers.map((m, idx) => (
          <g
            key={`marker-${idx}`}
            onMouseEnter={() => setHoveredIdx(idx)}
            onMouseLeave={() => setHoveredIdx(null)}
            className="cursor-pointer"
          >
            {m.isMissing ? (
              <g>
                <circle cx={m.x} cy={m.y} r="5" fill="rgba(245, 158, 11, 0.2)" stroke="#F59E0B" strokeWidth="2" />
                <line
                  x1={m.x - 2}
                  y1={m.y - 2}
                  x2={m.x + 2}
                  y2={m.y + 2}
                  stroke="#F59E0B"
                  strokeWidth="1.5"
                />
              </g>
            ) : (
              <circle
                cx={m.x}
                cy={m.y}
                r={hoveredIdx === idx ? 4.5 : 3}
                fill="#00D09C"
                stroke="#0b111e"
                strokeWidth="1.5"
              />
            )}
          </g>
        ))}
      </svg>

      {/* Mini Tooltip */}
      {hoveredIdx !== null && (
        <div
          className="absolute z-20 pointer-events-none transform -translate-x-1/2 -translate-y-full bg-[#1b2a47] text-white text-[11px] py-1 px-2.5 rounded shadow-drawer border border-[#2a3d5d] whitespace-nowrap"
          style={{
            left: `${((markers[hoveredIdx].x / width) * 100).toFixed(1)}%`,
            top: `${Math.max(0, markers[hoveredIdx].y - 6)}px`,
          }}
        >
          <div className="font-bold font-display">{markers[hoveredIdx].week}</div>
          <div className={`font-mono ${markers[hoveredIdx].isMissing ? 'text-friction-dark' : 'text-primary'}`}>
            {markers[hoveredIdx].isMissing
              ? 'No review data (0 reviews)'
              : `${markers[hoveredIdx].count} reviews`}
          </div>
        </div>
      )}
    </div>
  );
};
