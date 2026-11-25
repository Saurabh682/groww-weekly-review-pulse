import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { matchRoutes } from 'react-router-dom';
import { routes } from '../src/app/router';
import { STATUS_BADGES } from '../src/components/AppStatusBadge';
import { HELP_FACTS, LIVE_APP_FAQS, LIVE_APP_FEATURES, SCHEDULE } from '../src/features/help/liveApps';
import { TREND_WEEKS } from '../src/lib/themeTrend';
import { app, FakeApi } from './fakeApi';
import { openRoute } from './openRoute';

const PROJECT = path.resolve(__dirname, '../..');
const IST_OFFSET_MINUTES = 330;
const MINUTES_PER_HOUR = 60;
const HOURS_PER_DAY = 24;

const project = (file: string) => readFileSync(path.join(PROJECT, file), 'utf-8');

function setting(name: string): number {
  return Number(project('config/pulse.yaml').match(new RegExp(`^  ${name}: (\\d+)`, 'm'))?.[1]);
}

function indiaTime(cron: string): string {
  const [minute, hour] = cron.split(' ').map(Number);
  const total = hour * MINUTES_PER_HOUR + minute + IST_OFFSET_MINUTES;
  const two = (n: number) => String(n).padStart(2, '0');
  return `${two(Math.floor(total / MINUTES_PER_HOUR) % HOURS_PER_DAY)}:${two(total % MINUTES_PER_HOUR)}`;
}

const everyWord = () => JSON.stringify([LIVE_APP_FEATURES, LIVE_APP_FAQS]);

beforeEach(() => {
  new FakeApi().apps(app('groww', 'Groww')).install();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('what Help says about live apps', () => {
  it('test_HLP_01_matches_the_settings', () => {
    expect(HELP_FACTS).toEqual({
      slots: Number(project('src/registry/service.py').match(/^ACTIVE_APP_CAP = (\d+)/m)?.[1]),
      minReviews: setting('min_reviews'),
      windowWeeks: setting('weeks'),
      maxThemes: setting('max_themes'),
      topThemes: setting('top_n'),
      trendWeeks: TREND_WEEKS,
    });
  });

  it('test_HLP_02_matches_the_schedule', () => {
    const crons = [...project('.github/workflows/pulse.yml').matchAll(/cron: "([^"]+)"/g)].map(([, cron]) => cron);
    expect(Object.values(SCHEDULE).map(({ cron }) => cron)).toEqual(crons);
    Object.values(SCHEDULE).forEach(({ cron, text }) => {
      expect(text).toContain(indiaTime(cron));
      expect(everyWord()).toContain(text);
    });
  });

  it('test_HLP_03_explains_every_status', () => {
    const entry = LIVE_APP_FEATURES.find(({ id }) => id === 'feat-app-status')!;
    Object.values(STATUS_BADGES).forEach(({ text }) =>
      expect(entry.keyCapabilities.filter((line) => line.startsWith(`${text}: `))).toHaveLength(1),
    );
    expect(entry.keyCapabilities.filter((line) => line.startsWith('Not enough reviews yet: '))).toHaveLength(1);
  });

  it('starts every step with a short label', () => {
    LIVE_APP_FEATURES.flatMap(({ workflow }) => workflow).forEach((step) => expect(step).toMatch(/^[A-Z][^:.]{2,40}: \S/));
  });

  it('gives every entry its own id', () => {
    const ids = [...LIVE_APP_FEATURES, ...LIVE_APP_FAQS].map(({ id }) => id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('Help page', () => {
  it('test_HLP_04_lists_live_app_entries_first', async () => {
    openRoute('/help');
    const titles = (await screen.findAllByRole('heading', { level: 3 })).map((heading) => heading.textContent);
    expect(titles.slice(0, LIVE_APP_FEATURES.length)).toEqual(LIVE_APP_FEATURES.map(({ title }) => title));
  });

  it('shows only live app entries when that topic is chosen', async () => {
    openRoute('/help');
    await userEvent.click(await screen.findByRole('button', { name: 'Your Apps' }));
    expect(screen.getByText(`${LIVE_APP_FEATURES.length} comprehensive feature specifications`)).toBeInTheDocument();
    expect(screen.getByText(`${LIVE_APP_FAQS.length} answers available`)).toBeInTheDocument();
  });

  it('finds the answer for an app without a pulse', async () => {
    openRoute('/help');
    await userEvent.type(await screen.findByRole('textbox'), 'no pulse');
    const question = screen.getByRole('button', { name: /Why does an app have no pulse yet\?/ });
    await userEvent.click(question);
    expect(within(question.parentElement!).getByText(/fewer than 30 reviews/)).toBeInTheDocument();
  });

  it.each(['/apps/groww', '/manage'])('opens Help from %s', async (from) => {
    const { currentPath } = openRoute(from);
    await userEvent.click(within(await screen.findByRole('banner')).getByRole('button', { name: 'Help' }));
    expect(currentPath()).toBe('/help');
  });

  it('test_HLP_05_links_lead_to_pages_that_use_them', async () => {
    openRoute('/help');
    const links = await screen.findAllByRole('link', { name: 'Launch →' });
    expect(links.length).toBeGreaterThan(0);
    links.forEach((link) => {
      const target = new URL(link.getAttribute('href')!, 'http://help.test');
      const leaf = matchRoutes(routes, target.pathname)!.slice(-1)[0];
      expect(['/sample', '/run', '/import', '/themes']).toContain(leaf.pathname);
    });
    expect(screen.queryByText('Path: /')).toBeNull();
  });
});
