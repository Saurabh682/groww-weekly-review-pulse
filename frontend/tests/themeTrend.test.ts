import { describe, expect, it } from 'vitest';
import { addWeeks } from '../src/lib/dates';
import { buildThemeTrend, TREND_WEEKS } from '../src/lib/themeTrend';
import { pulse } from './fakeApi';

const LATEST = '2026-11-16';

describe('buildThemeTrend', () => {
  it('is empty without pulses', () => {
    expect(buildThemeTrend([])).toEqual({ weeks: [], series: [] });
  });

  it('puts weeks in time order and shares in percent', () => {
    const trend = buildThemeTrend([pulse(LATEST, { A: 0.5 }), pulse('2026-11-09', { A: 0.25 })]);
    expect(trend).toEqual({ weeks: ['2026-11-09', LATEST], series: [{ label: 'A', shares: [25, 50] }] });
  });

  it('leaves a gap for a week without a pulse and for a theme that was not there', () => {
    const trend = buildThemeTrend([pulse(LATEST, { A: 0.5 }), pulse('2026-11-02', { A: 0.25, B: 0.125 })]);
    expect(trend.weeks).toEqual(['2026-11-02', '2026-11-09', LATEST]);
    expect(trend.series).toEqual([
      { label: 'A', shares: [25, null, 50] },
      { label: 'B', shares: [12.5, null, null] },
    ]);
  });

  it('never looks further back than eight weeks', () => {
    const pulses = Array.from({ length: 12 }, (_, i) => pulse(addWeeks(LATEST, -i), { [`T${i}`]: 0.5 }));
    const trend = buildThemeTrend(pulses);
    expect(trend.weeks).toHaveLength(TREND_WEEKS);
    expect(trend.series.map((s) => s.label)).toEqual(['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']);
  });

  it('orders by the newest share, whatever the order of the pulses', () => {
    const now = pulse(LATEST, { A: 0.25, B: 0.5 });
    const before = pulse('2026-11-09', { A: 0.75, B: 0.125 });
    expect(buildThemeTrend([now, before])).toEqual(buildThemeTrend([before, now]));
    expect(buildThemeTrend([before, now]).series.map((s) => s.label)).toEqual(['B', 'A']);
  });
});
