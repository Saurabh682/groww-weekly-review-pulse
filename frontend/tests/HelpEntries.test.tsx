import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { matchRoutes } from 'react-router-dom';
import { routes } from '../src/app/router';
import { STATUS_BADGES } from '../src/components/AppStatusBadge';
import { HELP_TOPICS } from '../src/features/help/entries';
import { HOW_IT_WORKS_FAQS, HOW_IT_WORKS_FEATURES, NOTE_FACTS, RANK_FORMULA } from '../src/features/help/howItWorks';
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

function number(file: string, pattern: RegExp): number {
  return Number(project(file).match(pattern)?.[1]);
}

const ALL_FEATURES = [...LIVE_APP_FEATURES, ...HOW_IT_WORKS_FEATURES];
const ALL_FAQS = [...LIVE_APP_FAQS, ...HOW_IT_WORKS_FAQS];
const everyWord = () => JSON.stringify([ALL_FEATURES, ALL_FAQS]);

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
    const ids = [...ALL_FEATURES, ...ALL_FAQS].map(({ id }) => id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

describe('what Help says about how the pulse works', () => {
  it('test_HLP_06_matches_the_note_checks', () => {
    const quoteWords = project('src/note/validate.py').match(/between (\d+) and (\d+) words/)!;
    expect(NOTE_FACTS).toEqual({
      maxWords: setting('max_words'),
      quotes: setting('quotes'),
      actions: setting('actions'),
      quoteMinWords: Number(quoteWords[1]),
      quoteMaxWords: Number(quoteWords[2]),
      actionMaxWords: number('src/note/validate.py', /act_words > (\d+):/),
      minClusterSharePct: Math.round(Number(project('config/pulse.yaml').match(/^  min_cluster_share: ([\d.]+)/m)?.[1]) * 100),
      groupOverWords: number('src/themes/filter.py', /min_word_count: int = (\d+)/),
      shortCoverageWeeks: number('src/clean/window.py', /^SHORT_COVERAGE_WEEKS = (\d+)/m),
    });
    expect(number('src/note/validate.py', /if wc > (\d+):/)).toBe(NOTE_FACTS.maxWords);
  });

  it('test_HLP_07_matches_the_ranking', () => {
    const [, base, weight] = project('src/themes/rank.py').match(/priority_score = round\(share_pct \* \(([\d.]+) \+ ([\d.]+) \* neg_share\)/)!;
    expect(RANK_FORMULA).toBe(`share × (${base} + ${weight} × negative share)`);
  });

  it('test_HLP_08_never_claims_the_system_can_send', () => {
    const capabilities = project('src/mcp/capabilities.py');
    expect(capabilities).toMatch(/MANDATORY_DENIED_PATTERNS = \([^)]*"SEND"/);
    const allowed = capabilities.match(/REQUIRED_CAPABILITIES = \(([^)]*)\)/)![1];
    expect(allowed.toLowerCase()).not.toContain('send');
    expect(everyWord().toLowerCase()).not.toMatch(/gmail\.send|send scope|sends? (the|an|your) email automatically/);
  });

  it('test_HLP_09_every_topic_has_entries', () => {
    HELP_TOPICS.forEach(({ id }) => {
      expect(ALL_FEATURES.some(({ category }) => category === id)).toBe(true);
      expect(ALL_FAQS.some(({ category }) => category === id)).toBe(true);
    });
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
    await userEvent.click(await screen.findByRole('button', { name: 'Your apps' }));
    expect(screen.getByText(`${LIVE_APP_FEATURES.length} features`)).toBeInTheDocument();
    expect(screen.getByText(`${LIVE_APP_FAQS.length} answers available`)).toBeInTheDocument();
  });

  it('finds the answer for an app without a pulse', async () => {
    openRoute('/help');
    await userEvent.type(await screen.findByRole('textbox', { name: 'Search Help' }), 'no pulse');
    const question = screen.getByRole('button', { name: /Why does an app have no pulse yet\?/ });
    await userEvent.click(question);
    expect(within(question.parentElement!).getByText(/fewer than 30 reviews/)).toBeInTheDocument();
  });

  it.each(['/apps/groww', '/manage'])('opens Help from %s', async (from) => {
    const { currentPath } = openRoute(from);
    await userEvent.click(within(await screen.findByRole('banner')).getByRole('button', { name: 'Help' }));
    expect(currentPath()).toBe('/help');
  });

  it('test_HLP_10_shows_whole_questions', async () => {
    openRoute('/help');
    const question = await screen.findByRole('button', { name: /How long until a new app shows something\?/ });
    expect(question).toHaveAttribute('aria-expanded', 'false');
    expect(within(question).getByText('How long until a new app shows something?')).not.toHaveClass('truncate');
    await userEvent.click(question);
    expect(question).toHaveAttribute('aria-expanded', 'true');
  });

  it('test_UIC_06_details_report_open_or_closed', async () => {
    openRoute('/help');
    const [details] = await screen.findAllByRole('button', { name: 'Show details' });
    expect(details).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(details);
    expect(details).toHaveAttribute('aria-expanded', 'true');
    expect(details).toHaveTextContent('Hide details');
    expect(document.getElementById(details.getAttribute('aria-controls')!)).toHaveTextContent('Steps');
  });

  it('test_UIC_07_says_when_nothing_matches', async () => {
    openRoute('/help');
    await userEvent.type(await screen.findByRole('textbox', { name: 'Search Help' }), 'zzzz');
    expect(screen.getByRole('heading', { name: 'Nothing matches' })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Show everything' }));
    expect(screen.getByRole('textbox', { name: 'Search Help' })).toHaveValue('');
  });

  it('test_HLP_11_phone_menu_reaches_manage_apps', async () => {
    const { currentPath } = openRoute('/apps/groww');
    await userEvent.click(within(await screen.findByRole('navigation', { name: 'Mobile' })).getByRole('link', { name: /Manage apps/ }));
    expect(currentPath()).toBe('/manage');
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
