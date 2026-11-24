import { PulseWeek } from '../data/types';
import { addWeeks } from './dates';

export const TREND_WEEKS = 8;
const PERCENT = 100;

export interface ThemeSeries {
  label: string;
  shares: (number | null)[];
}

export interface ThemeTrend {
  weeks: string[];
  series: ThemeSeries[];
}

function weekSpan(pulses: PulseWeek[]): string[] {
  const starts = pulses.map((p) => p.week_start).sort();
  const latest = starts[starts.length - 1];
  return Array.from({ length: TREND_WEEKS }, (_, i) => addWeeks(latest, i + 1 - TREND_WEEKS)).filter(
    (week) => week >= starts[0],
  );
}

function byNewestShare(a: ThemeSeries, b: ThemeSeries): number {
  for (let i = a.shares.length - 1; i >= 0; i -= 1) {
    const difference = (b.shares[i] ?? -1) - (a.shares[i] ?? -1);
    if (difference !== 0) return difference;
  }
  return a.label.localeCompare(b.label);
}

export function buildThemeTrend(pulses: PulseWeek[]): ThemeTrend {
  if (pulses.length === 0) return { weeks: [], series: [] };
  const weeks = weekSpan(pulses);
  const themesByWeek = new Map(pulses.map((p) => [p.week_start, p.themes]));
  const labels = new Set(weeks.flatMap((week) => themesByWeek.get(week)?.map((t) => t.label) ?? []));
  const series = [...labels].map((label) => ({
    label,
    shares: weeks.map((week) => {
      const theme = themesByWeek.get(week)?.find((t) => t.label === label);
      return theme ? theme.share_pct * PERCENT : null;
    }),
  }));
  return { weeks, series: series.sort(byNewestShare) };
}
