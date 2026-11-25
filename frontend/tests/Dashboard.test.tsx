import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RETRY_DELAY_MS, SLOW_RESPONSE_MS, WAKE_LIMIT_MS } from '../src/data/apiClient';
import { PulseAttempt } from '../src/data/types';
import { REFRESH_MS } from '../src/data/useApi';
import { app, FakeApi, history, pulse, run } from './fakeApi';
import { openRoute } from './openRoute';

const GROWW = app('groww', 'Groww');
const COIN = app('zerodha-coin', 'Zerodha Coin');
const OLD = app('old', 'Old App', 'archived');
const WEEK = '2026-11-16';
const APPS = '/apps?include_archived=true';
const PULSES = (key: string) => `/apps/${key}/pulses?limit=12`;
const LOW_VOLUME: PulseAttempt = {
  week_start: WEEK,
  status: 'low_volume',
  window_start: '2026-08-31',
  window_end: '2026-11-22',
  usable_reviews: 7,
  min_reviews: 30,
};

let api: FakeApi;

function page() {
  return within(screen.getByRole('main'));
}

function interactiveElements(container: HTMLElement): HTMLElement[] {
  return [...container.querySelectorAll<HTMLElement>('a, button, input, select, textarea, summary')];
}

function expectNamed(container: HTMLElement) {
  interactiveElements(container).forEach((element) => expect(element).toHaveAccessibleName());
}

beforeEach(() => {
  api = new FakeApi()
    .apps(GROWW, COIN, OLD)
    .shows(GROWW, [pulse(WEEK, { 'Charges & Pricing': 0.557, 'Customer Support': 0.21 })])
    .shows(COIN, [pulse(WEEK, { 'Mutual Funds & SIPs': 0.236 }, { total_reviews: 75 })])
    .shows(OLD, [])
    .install();
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('choosing an app', () => {
  it('opens the first active app from /', async () => {
    const { currentPath } = openRoute('/');
    expect(await screen.findByRole('heading', { level: 1, name: 'Groww' })).toBeInTheDocument();
    expect(currentPath()).toBe('/apps/groww');
  });

  it('skips a failed app when another one is active', async () => {
    api.apps(app('broken', 'Broken', 'failed'), COIN);
    const { currentPath } = openRoute('/');
    await screen.findByRole('heading', { level: 1, name: 'Zerodha Coin' });
    expect(currentPath()).toBe('/apps/zerodha-coin');
  });

  it('test_DSH_01_app_switch', async () => {
    const { currentPath } = openRoute('/apps/groww');
    await page().findByText('Charges & Pricing');
    await userEvent.click(screen.getByRole('button', { name: 'Choose app: Groww' }));
    await userEvent.click(screen.getByRole('button', { name: 'Zerodha Coin' }));

    expect(currentPath()).toBe('/apps/zerodha-coin');
    expect(page().queryByText('Charges & Pricing')).toBeNull();
    expect(await page().findByText('Mutual Funds & SIPs')).toBeInTheDocument();
    expect(page().getByRole('heading', { level: 1 })).toHaveTextContent('Zerodha Coin');
    expect(page().queryByText('Charges & Pricing')).toBeNull();
    expect(screen.getByRole('button', { name: 'Choose app: Zerodha Coin' })).toBeInTheDocument();
  });

  it('never shows a late answer for the app that was left', async () => {
    api.on('/apps/zerodha-coin/pulses?limit=12', 'never');
    openRoute('/apps/groww');
    await page().findByText('Charges & Pricing');
    await userEvent.click(screen.getByRole('button', { name: 'Choose app: Groww' }));
    await userEvent.click(screen.getByRole('button', { name: 'Zerodha Coin' }));
    expect(page().queryByText('Charges & Pricing')).toBeNull();
    expect(page().getByRole('status', { name: 'Loading' })).toBeInTheDocument();
  });

  it('lists archived apps only when asked', async () => {
    openRoute('/apps/groww');
    await page().findByText('Charges & Pricing');
    await userEvent.click(screen.getByRole('button', { name: 'Choose app: Groww' }));
    expect(screen.getByText('2 of 5 app slots used')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Old App/ })).toBeNull();
    await userEvent.click(screen.getByRole('checkbox', { name: 'Show archived apps' }));
    expect(screen.getByRole('button', { name: /Old App/ })).toBeInTheDocument();
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByRole('button', { name: /Old App/ })).toBeNull();
  });

  it.each(['/help', '/themes', '/run', '/import', '/sample'])('keeps the picker on %s', async (path) => {
    openRoute(path);
    expect(await screen.findByRole('button', { name: 'Choose app: Choose an app' })).toBeInTheDocument();
  });
});

describe('app states', () => {
  it('test_DSH_02_unknown_or_archived', async () => {
    const unknown = openRoute('/apps/nope');
    expect(await page().findByText('App not found')).toBeInTheDocument();
    expect(page().getByRole('link', { name: 'Groww' })).toHaveAttribute('href', '/apps/groww');
    expect(page().queryByRole('link', { name: 'Old App' })).toBeNull();
    unknown.unmount();

    openRoute('/apps/old');
    expect(await page().findByRole('heading', { level: 1, name: 'Old App' })).toBeInTheDocument();
    expect(page().getByText('Archived')).toBeInTheDocument();
    expect(page().getByText(/This page is read-only/)).toBeInTheDocument();
  });

  it('test_DSH_03_backfilling_state', async () => {
    const fresh = app('fresh', 'Fresh', 'backfilling');
    api.apps(fresh).shows(fresh, [], { collections: { play_store: null, app_store: null }, runs: [], stores: [] });
    openRoute('/apps/fresh');
    expect(await page().findByText('Collecting reviews for Fresh')).toBeInTheDocument();
    expect(page().queryByRole('img')).toBeNull();
    expect(page().queryByRole('table')).toBeNull();
    expect(page().queryByText('Theme share, last 8 weeks')).toBeNull();
  });

  it.each([
    ['active', /after the next run/],
    ['failed', /daily run tries again/],
    ['archived', /archived before its first pulse/],
  ] as const)('says what happens next when an app that is %s has no pulse', async (status, next) => {
    const quiet = app('quiet', 'Quiet', status);
    api.apps(quiet).shows(quiet, []);
    openRoute('/apps/quiet');
    const card = (await page().findByText('No pulse')).parentElement!;
    expect(card).toHaveTextContent(next);
  });

  it('test_DSH_19_low_volume_state', async () => {
    const small = app('small', 'Small');
    api.apps(small).shows(small, []).on(PULSES('small'), { body: history(small, [], { latest_run: LOW_VOLUME }) });
    openRoute('/apps/small');
    const card = (await page().findByText('Not enough reviews yet')).parentElement!;
    expect(card).toHaveTextContent('A pulse needs 30 reviews with enough text. Small has 7 from 31 Aug 2026 to 22 Nov 2026.');
    expect(card).toHaveTextContent('checked again every Monday');
    expect(page().queryByText(/after the next run/)).toBeNull();
  });

  it('says when the last collection failed and keeps the last pulse', async () => {
    const broken = app('broken', 'Broken', 'failed');
    api.apps(broken).shows(broken, [pulse(WEEK, { Charges: 0.4 })]);
    openRoute('/apps/broken');
    expect(await page().findByRole('alert')).toHaveTextContent('The last collection failed');
    expect(page().getByText('Charges')).toBeInTheDocument();
  });

  it('test_DSH_04_waking_backend', async () => {
    vi.useFakeTimers();
    api.on('/apps?include_archived=true', 'offline', { status: 503 }, {
      body: { slots_used: 1, slots_total: 5, apps: [GROWW] },
    });
    openRoute('/apps/groww');
    await act(() => vi.advanceTimersByTimeAsync(1));
    expect(page().getByText('Waking backend')).toBeInTheDocument();
    await act(() => vi.advanceTimersByTimeAsync(2 * RETRY_DELAY_MS));
    expect(page().getByRole('heading', { level: 1, name: 'Groww' })).toBeInTheDocument();
  });

  it('calls a slow first answer waking', async () => {
    vi.useFakeTimers();
    api.on('/apps?include_archived=true', 'never');
    openRoute('/apps/groww');
    await act(() => vi.advanceTimersByTimeAsync(SLOW_RESPONSE_MS - 1));
    expect(page().queryByText('Waking backend')).toBeNull();
    await act(() => vi.advanceTimersByTimeAsync(1));
    expect(page().getByText('Waking backend')).toBeInTheDocument();
  });

  it('calls a slow panel loading once the backend has answered', async () => {
    vi.useFakeTimers();
    api.on('/apps/groww/health', 'never');
    openRoute('/apps/groww');
    await act(() => vi.advanceTimersByTimeAsync(2 * SLOW_RESPONSE_MS));
    expect(page().getByText('Charges & Pricing')).toBeInTheDocument();
    expect(page().queryByText('Waking backend')).toBeNull();
    expect(page().getByRole('status', { name: 'Loading' })).toBeInTheDocument();
  });

  it('gives up waking after the limit and retries on request', async () => {
    vi.useFakeTimers();
    api.on('/apps?include_archived=true', 'offline');
    openRoute('/apps/groww');
    await act(() => vi.advanceTimersByTimeAsync(WAKE_LIMIT_MS + RETRY_DELAY_MS));
    expect(page().getByRole('alert')).toHaveTextContent('did not wake up');
    api.apps(GROWW);
    await act(async () => page().getByRole('button', { name: 'Retry' }).click());
    await act(() => vi.advanceTimersByTimeAsync(1));
    expect(page().getByRole('heading', { level: 1, name: 'Groww' })).toBeInTheDocument();
  });

  it.each([
    [{ status: 500, body: { error: 'Store is down' } }, 'Store is down'],
    [{ status: 200, contentType: 'text/html' }, 'unexpected answer'],
  ])('reports an answer it cannot use: %j', async (answer, message) => {
    api.on('/apps/groww/pulses?limit=12', answer);
    openRoute('/apps/groww');
    expect(await page().findByRole('alert')).toHaveTextContent(message);
  });

  it('says when the build has no data address', async () => {
    vi.stubEnv('VITE_API_URL', '');
    openRoute('/');
    expect(await page().findByRole('alert')).toHaveTextContent('Set VITE_API_URL');
    expect(api.calls).toEqual([]);
  });
});

describe('keeping an open page up to date', () => {
  const FRESH = app('fresh', 'Fresh', 'backfilling');
  const FRESH_ACTIVE = app('fresh', 'Fresh');
  const list = (of: typeof FRESH) => ({ body: { slots_used: 1, slots_total: 5, apps: [of] } });
  const requests = (path: string) => api.calls.filter((call) => call === path).length;
  const wait = (ms: number) => act(() => vi.advanceTimersByTimeAsync(ms));

  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('test_DSH_20_waiting_page_fills_in', async () => {
    api.shows(FRESH, [pulse(WEEK, { Charges: 0.4 })])
      .on(APPS, list(FRESH), list(FRESH_ACTIVE))
      .on(
        PULSES('fresh'),
        { body: history(FRESH, []) },
        { body: history(FRESH, [], { latest_run: { ...LOW_VOLUME, status: 'running' } }) },
        { body: history(FRESH, [pulse(WEEK, { Charges: 0.4 })]) },
      );
    openRoute('/apps/fresh');
    await wait(1);
    expect(page().getByText('Collecting reviews for Fresh')).toBeInTheDocument();
    await wait(REFRESH_MS);
    expect(requests('/apps/fresh/health')).toBe(2);
    expect(page().queryByText('Collecting reviews for Fresh')).toBeNull();
    expect(page().getByText('No pulse')).toBeInTheDocument();
    await wait(REFRESH_MS);
    expect(page().getByText('Charges')).toBeInTheDocument();
  });

  it('shows an app when the API is older than the page and sends no latest run', async () => {
    api.apps(FRESH_ACTIVE).shows(FRESH_ACTIVE, []).on(PULSES('fresh'), { body: { app_key: 'fresh', pulses: [] } });
    openRoute('/apps/fresh');
    await wait(1);
    expect(page().getByText('No pulse')).toBeInTheDocument();
  });

  it('stops asking once the first run has an answer', async () => {
    api.apps(FRESH_ACTIVE).shows(FRESH_ACTIVE, []).on(PULSES('fresh'), { body: history(FRESH, [], { latest_run: LOW_VOLUME }) });
    openRoute('/apps/fresh');
    await wait(1);
    const asked = api.calls.length;
    await wait(3 * REFRESH_MS);
    expect(api.calls).toHaveLength(asked);
  });

  it('does not ask while the tab is hidden, and asks when it is opened again', async () => {
    const visible = vi.spyOn(document, 'visibilityState', 'get').mockReturnValue('hidden');
    api.shows(FRESH, []).on(APPS, list(FRESH), list(FRESH_ACTIVE));
    openRoute('/apps/fresh');
    await wait(1);
    await wait(3 * REFRESH_MS);
    expect(requests(APPS)).toBe(1);
    expect(page().getByText('Collecting reviews for Fresh')).toBeInTheDocument();
    visible.mockReturnValue('visible');
    document.dispatchEvent(new Event('visibilitychange'));
    await wait(1);
    expect(requests(APPS)).toBe(2);
    expect(page().queryByText('Collecting reviews for Fresh')).toBeNull();
  });

  it.each([[{ status: 500, body: { error: 'Store is down' } }], ['offline' as const]])(
    'keeps the page on screen when a refresh fails: %j',
    async (answer) => {
      api.on(PULSES('groww'), { body: history(GROWW, [pulse(WEEK, { Charges: 0.4 })]) }, answer);
      openRoute('/apps/groww');
      await wait(1);
      document.dispatchEvent(new Event('visibilitychange'));
      await wait(1);
      expect(requests(PULSES('groww'))).toBe(2);
      expect(page().getByText('Charges')).toBeInTheDocument();
      expect(page().queryByRole('alert')).toBeNull();
      expect(page().queryByText('Waking backend')).toBeNull();
    },
  );

  it('stops asking when the page is closed', async () => {
    api.shows(FRESH, []).on(APPS, list(FRESH));
    const added = vi.spyOn(document, 'addEventListener');
    const removed = vi.spyOn(document, 'removeEventListener');
    const listeners = (spy: typeof added | typeof removed) =>
      spy.mock.calls.filter(([type]) => type === 'visibilitychange').map(([, listener]) => listener);
    const started = vi.spyOn(globalThis, 'setInterval');
    const cleared = vi.spyOn(globalThis, 'clearInterval');
    const view = openRoute('/apps/fresh');
    await wait(1);
    view.unmount();
    expect(listeners(added).length).toBeGreaterThan(0);
    expect(listeners(removed)).toEqual(expect.arrayContaining(listeners(added)));
    const timers = started.mock.results.map(({ value }) => value);
    expect(timers.length).toBeGreaterThan(0);
    expect(cleared.mock.calls.map(([timer]) => timer)).toEqual(expect.arrayContaining(timers));
  });
});

describe('overview', () => {
  it('shows the latest pulse with its links', async () => {
    openRoute('/apps/groww');
    await page().findByText('Charges & Pricing');
    expect(page().getByRole('link', { name: 'Open Google Doc' })).toHaveAttribute(
      'href',
      `https://docs.google.com/document/d/${WEEK}/edit`,
    );
    expect(page().getByRole('link', { name: 'View Gmail draft' })).toBeInTheDocument();
    expect(screen.queryByText(/send email/i)).toBeNull();
    expect(page().getByText('4,736')).toBeInTheDocument();
    expect(page().getByText('55.7%')).toBeInTheDocument();
    expect(page().queryByText(/Short coverage/)).toBeNull();
  });

  it('hides links a pulse does not have', async () => {
    api.shows(GROWW, [pulse(WEEK, { Charges: 0.4 }, { status: 'validated', doc_url: null, draft_created: false, published_at: null })]);
    openRoute('/apps/groww');
    expect(await page().findByText('Not published')).toBeInTheDocument();
    expect(page().queryByRole('link')).toBeNull();
  });

  it('says why one pulse is not a trend', async () => {
    openRoute('/apps/groww');
    expect(await page().findByText(/starts when there are two weekly pulses/)).toBeInTheDocument();
    expect(page().queryByRole('img')).toBeNull();
  });

  it('draws one chart per theme once there are two weeks', async () => {
    api.shows(GROWW, [pulse(WEEK, { Charges: 0.5, Support: 0.2 }), pulse('2026-11-09', { Charges: 0.4 })]);
    openRoute('/apps/groww');
    expect(
      await page().findByRole('img', { name: 'Charges: share of reviews by week, 50.0% in the latest week' }),
    ).toBeInTheDocument();
    expect(page().getAllByRole('img')).toHaveLength(2);
  });

  it('test_DSH_08_health_flags', async () => {
    api.shows(GROWW, [pulse(WEEK, { Charges: 0.4 }, { short_coverage: true, coverage_weeks: 3.5 })], {
      collections: {
        play_store: run({ covered_start: '2026-11-20', source_limit_hit: true }),
        app_store: run({ platform: 'app_store', status: 'failed', covered_start: null, feed_gaps: 2, error: 'Feed answered 500' }),
      },
      stores: [{ platform: 'play_store', reviews: 10, caveat: 'partial, from 2026-11-20' }],
    });
    openRoute('/apps/groww');
    expect(await page().findByText('20 Nov 2026 to 24 Nov 2026')).toBeInTheDocument();
    expect(page().getByText('Store limit reached')).toBeInTheDocument();
    expect(page().getByText('Feed gaps: 2')).toBeInTheDocument();
    expect(page().getByText('Feed answered 500')).toBeInTheDocument();
    expect(page().getByText('Pulse: partial, from 2026-11-20')).toBeInTheDocument();
    expect(page().getByText(/span 3.5 weeks/)).toBeInTheDocument();
  });

  it('keeps the pulse visible when health fails', async () => {
    api.on('/apps/groww/health', { status: 500, body: { error: 'No health' } });
    openRoute('/apps/groww');
    expect(await page().findByRole('alert')).toHaveTextContent('No health');
    expect(page().getByText('Charges & Pricing')).toBeInTheDocument();
  });

  it('tells a store the app is not on from one with no run', async () => {
    const solo = app('solo', 'Solo', 'active', { app_store_id: null });
    api.apps(solo).shows(solo, [], { collections: { play_store: null, app_store: null }, runs: [], stores: [] });
    openRoute('/apps/solo');
    expect(await page().findByText('Not on this store')).toBeInTheDocument();
    expect(page().getByText('No run yet')).toBeInTheDocument();
  });
});

describe('past week', () => {
  const LATEST = pulse(WEEK, { Charges: 0.5 });
  const PAST = pulse('2026-11-09', { Support: 0.3 });

  it('opens a past week and comes back to the latest', async () => {
    api.shows(GROWW, [LATEST, PAST]);
    const { currentPath } = openRoute('/apps/groww');
    await userEvent.click(await screen.findByRole('button', { name: 'Choose week: Week of 16 Nov 2026' }));
    await userEvent.click(screen.getByRole('button', { name: 'Week of 9 Nov 2026' }));
    expect(await page().findByText('Support')).toBeInTheDocument();
    expect(currentPath()).toBe('/apps/groww/weeks/2026-11-09');
    expect(page().getByText('Reviews per store')).toBeInTheDocument();

    await userEvent.click(await screen.findByRole('button', { name: 'Choose week: Week of 9 Nov 2026' }));
    await userEvent.click(screen.getByRole('button', { name: /Week of 16 Nov 2026/ }));
    expect(await page().findByRole('heading', { name: 'Charges' })).toBeInTheDocument();
    expect(currentPath()).toBe('/apps/groww');
  });

  it('says when the app has no pulse for that week', async () => {
    openRoute('/apps/groww/weeks/2020-01-06');
    expect(await page().findByText('Week not found')).toBeInTheDocument();
    await userEvent.click(page().getByRole('button', { name: 'See the latest pulse' }));
    expect(await page().findByText('Charges & Pricing')).toBeInTheDocument();
  });
});

describe('sample pages', () => {
  it('mark their data as sample data and real pages do not', async () => {
    const sample = openRoute('/themes');
    expect(await screen.findByText('Themes Explorer', {}, { timeout: 2000 })).toBeInTheDocument();
    expect(within(screen.getByRole('banner')).getByText('Sample data')).toBeInTheDocument();
    sample.unmount();

    openRoute('/apps/groww');
    await page().findByText('Charges & Pricing');
    expect(within(screen.getByRole('banner')).queryByText('Sample data')).toBeNull();
    expect(screen.queryByText('Scenario Simulator')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Run pulse' })).toBeNull();
  });
});

describe('accessible names', () => {
  it.each(['/apps/groww', `/apps/groww/weeks/${WEEK}`, '/apps/nope', '/apps/old'])(
    'test_DSH_09_accessible_names %s',
    async (path) => {
      api.shows(GROWW, [pulse(WEEK, { Charges: 0.5 }), pulse('2026-11-09', { Charges: 0.4 })]);
      const { container } = openRoute(path);
      await page().findAllByRole('heading');
      await userEvent.click(screen.getByRole('button', { name: /^Choose app/ }));
      expect(interactiveElements(container).length).toBeGreaterThan(8);
      expectNamed(container);
    },
  );
});
