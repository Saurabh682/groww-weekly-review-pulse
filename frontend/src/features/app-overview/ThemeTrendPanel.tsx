import React, { useState } from 'react';
import { Card } from '../../components/Card';
import { EmptyState } from '../../components/EmptyState';
import { PulseWeek } from '../../data/types';
import { formatDay, formatShortDay } from '../../lib/dates';
import { formatShare } from '../../lib/format';
import { buildThemeTrend, ThemeSeries } from '../../lib/themeTrend';
import { SectionTitle } from '../../components/SectionTitle';

const WIDTH = 280;
const HEIGHT = 84;
const PAD = 8;
const AXIS_STEP = 20;
const MIN_WEEKS = 2;

interface Point {
  x: number;
  y: number;
}

function segments(points: (Point | null)[]): Point[][] {
  const runs: Point[][] = [[]];
  points.forEach((point) => {
    if (point) runs[runs.length - 1].push(point);
    else runs.push([]);
  });
  return runs.filter((run) => run.length > 1);
}

interface ThemeChartProps {
  series: ThemeSeries;
  weeks: string[];
  top: number;
}

const ThemeChart: React.FC<ThemeChartProps> = ({ series, weeks, top }) => {
  const [active, setActive] = useState<number | null>(null);
  const step = (WIDTH - 2 * PAD) / (weeks.length - 1);
  const points = series.shares.map((share, i) =>
    share === null ? null : { x: PAD + i * step, y: HEIGHT - PAD - (share / top) * (HEIGHT - 2 * PAD) },
  );
  const latest = series.shares[series.shares.length - 1];
  const shown = active ?? weeks.length - 1;
  const shownShare = series.shares[shown];

  return (
    <Card padding="tight">
      <h3 className="text-xs font-bold font-display text-white">{series.label}</h3>
      <p className="text-2xs font-mono text-text-secondary mt-0.5">
        {shownShare === null ? 'Not in the themes' : formatShare(shownShare)} • {formatShortDay(weeks[shown])}
      </p>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full mt-2"
        role="img"
        aria-label={`${series.label}: share of reviews by week, ${latest === null ? 'not in the latest week' : `${formatShare(latest)} in the latest week`}`}
        onMouseLeave={() => setActive(null)}
      >
        <line x1={PAD} x2={WIDTH - PAD} y1={PAD} y2={PAD} className="stroke-border" strokeWidth="1" />
        <line x1={PAD} x2={WIDTH - PAD} y1={HEIGHT - PAD} y2={HEIGHT - PAD} className="stroke-border" strokeWidth="1" />
        {active !== null && (
          <line
            x1={PAD + active * step}
            x2={PAD + active * step}
            y1={PAD}
            y2={HEIGHT - PAD}
            className="stroke-border-subtle"
            strokeWidth="1"
          />
        )}
        {segments(points).map((run) => (
          <polyline
            key={run[0].x}
            points={run.map((p) => `${p.x},${p.y}`).join(' ')}
            fill="none"
            className="stroke-primary"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
        {points.map(
          (point, i) =>
            point && (
              <circle
                key={weeks[i]}
                cx={point.x}
                cy={point.y}
                r={i === shown ? 5 : 4}
                className="fill-primary stroke-surface"
                strokeWidth="2"
              />
            ),
        )}
        {weeks.map((week, i) => (
          <rect
            key={week}
            x={PAD + (i - 0.5) * step}
            y="0"
            width={step}
            height={HEIGHT}
            fill="transparent"
            onMouseEnter={() => setActive(i)}
          />
        ))}
      </svg>
      <div className="flex justify-between text-3xs font-mono text-text-muted">
        <span>{formatShortDay(weeks[0])}</span>
        <span>0 to {top}%</span>
        <span>{formatShortDay(weeks[weeks.length - 1])}</span>
      </div>
    </Card>
  );
};

interface ThemeTrendPanelProps {
  pulses: PulseWeek[];
}

export const ThemeTrendPanel: React.FC<ThemeTrendPanelProps> = ({ pulses }) => {
  const { weeks, series } = buildThemeTrend(pulses);
  const highest = Math.max(0, ...series.flatMap((s) => s.shares.map((share) => share ?? 0)));
  const top = Math.max(AXIS_STEP, Math.ceil(highest / AXIS_STEP) * AXIS_STEP);

  return (
    <section>
      <SectionTitle>Theme share, last 8 weeks</SectionTitle>
      {weeks.length < MIN_WEEKS ? (
        <EmptyState headingLevel={3}
          compact
          title="No trend yet"
          description={`The trend starts when there are two weekly pulses. This app has ${weeks.length} so far.`}
        />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {series.map((s) => (
              <ThemeChart key={s.label} series={s} weeks={weeks} top={top} />
            ))}
          </div>
          <details className="text-xs text-text-secondary">
            <summary className="cursor-pointer font-semibold hover:text-white">Show as a table</summary>
            <div className="overflow-x-auto mt-2">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-border text-2xs font-mono font-bold text-text-muted uppercase tracking-wider">
                    <th className="py-3 px-4">Week</th>
                    {series.map((s) => (
                      <th key={s.label} className="py-3 px-4 text-right">
                        {s.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {weeks.map((week, i) => (
                    <tr key={week}>
                      <td className="py-3.5 px-4 whitespace-nowrap">{formatDay(week)}</td>
                      {series.map((s) => {
                        const share = s.shares[i];
                        return (
                          <td key={s.label} className="py-3.5 px-4 text-right">
                            {share === null ? '–' : formatShare(share)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
      )}
    </section>
  );
};
