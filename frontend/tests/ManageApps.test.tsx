import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { app, AUTH_URL, candidate, FakeApi, OPERATOR_TOKEN, signIn, storeSearch } from './fakeApi';
import { openRoute } from './openRoute';

const GROWW = app('groww', 'Groww');
const COIN = app('zerodha-coin', 'Zerodha Coin');
const OLD = app('old', 'Old App', 'archived');
const KITE = app('kite', 'Kite', 'pending_backfill');
const FULL = ['a', 'b', 'c', 'd', 'e'].map((key) => app(key, `App ${key.toUpperCase()}`));

const KITE_SEARCH = {
  term: 'Kite',
  country: 'in',
  no_matches: false,
  stores: {
    play_store: storeSearch('play_store', { candidates: [candidate('play_store', 'com.zerodha.kite3', 'Kite by Zerodha')] }),
    app_store: storeSearch('app_store', { candidates: [candidate('app_store', '1449453802', 'Zerodha Kite')] }),
  },
};

const REGISTERED = {
  app: KITE,
  slots_used: 3,
  slots_total: 5,
  backfill_dispatch: { status: 'not_configured', detail: null, message: 'Backfill is queued for the next daily run.' },
};

let api: FakeApi;

function page() {
  return within(screen.getByRole('main'));
}

function dialog() {
  return within(screen.getByRole('dialog'));
}

function store(name: string) {
  return within(dialog().getByRole('group', { name }));
}

function named(container: HTMLElement) {
  container
    .querySelectorAll<HTMLElement>('a, button, input, select, textarea, summary')
    .forEach((element) => expect(element).toHaveAccessibleName());
}

async function openManage() {
  const view = openRoute('/manage');
  await page().findByRole('heading', { level: 1, name: 'Manage apps' });
  return view;
}

async function openAsOperator() {
  signIn();
  const view = await openManage();
  await page().findByRole('button', { name: 'Add app' });
  return view;
}

async function searchFor(name: string) {
  await userEvent.type(dialog().getByRole('textbox', { name: 'App name' }), name);
  await userEvent.click(dialog().getByRole('button', { name: 'Search stores' }));
  await dialog().findByRole('group', { name: 'Google Play' });
}

beforeEach(() => {
  localStorage.clear();
  window.history.replaceState({}, '', '/');
  api = new FakeApi().apps(GROWW, COIN, OLD).on('POST /search', { body: KITE_SEARCH }).install();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe('signed out', () => {
  it('test_DSH_10_signed_out_manage', async () => {
    const { container } = await openManage();
    expect(await page().findByRole('heading', { name: 'Operator sign-in' })).toBeInTheDocument();
    expect(await page().findByRole('textbox', { name: 'Email' })).toBeInTheDocument();
    expect(page().getByRole('link', { name: 'Groww' })).toHaveAttribute('href', '/apps/groww');
    expect(page().getByText('2 of 5 slots used')).toBeInTheDocument();
    expect(page().queryByRole('button', { name: /Add app|Rename|Replace|Archive/ })).toBeNull();
    named(container);
  });

  it('asks for a link that cannot create an account', async () => {
    api.on(`POST ${AUTH_URL}/auth/v1/otp`, { body: {} });
    await openManage();
    await userEvent.type(await page().findByRole('textbox', { name: 'Email' }), 'operator@example.com');
    await userEvent.click(page().getByRole('button', { name: 'Email me a sign-in link' }));
    expect(await page().findByRole('status', { name: 'Sign-in link' })).toHaveTextContent('If this address belongs to an operator');
    const [sent] = api.sent;
    expect(sent.path).toBe(`POST ${AUTH_URL}/auth/v1/otp`);
    expect(sent.body).toMatchObject({ email: 'operator@example.com', create_user: false, code_challenge_method: 's256' });
  });

  it('does not reveal whether an address is an operator', async () => {
    api.on(`POST ${AUTH_URL}/auth/v1/otp`, {
      status: 422,
      body: { code: 'otp_disabled', error_code: 'otp_disabled', msg: 'Signups not allowed for otp' },
    });
    await openManage();
    await userEvent.type(await page().findByRole('textbox', { name: 'Email' }), 'stranger@example.com');
    await userEvent.click(page().getByRole('button', { name: 'Email me a sign-in link' }));
    expect(await page().findByRole('status', { name: 'Sign-in link' })).toHaveTextContent('If this address belongs to an operator');
    expect(page().queryByRole('alert')).toBeNull();
  });

  it('says when the link could not be sent', async () => {
    api.on(`POST ${AUTH_URL}/auth/v1/otp`, {
      status: 429,
      body: { code: 'over_email_send_rate_limit', error_code: 'over_email_send_rate_limit', msg: 'email rate limit exceeded' },
    });
    await openManage();
    await userEvent.type(await page().findByRole('textbox', { name: 'Email' }), 'operator@example.com');
    await userEvent.click(page().getByRole('button', { name: 'Email me a sign-in link' }));
    expect(await page().findByRole('alert')).toHaveTextContent('email rate limit exceeded');
  });

  it.each(['?code=abc', '?error=access_denied&error_code=otp_expired', '#error=access_denied&error_code=otp_expired'])(
    'says when a sign-in link did not work: %s',
    async (suffix) => {
      window.history.replaceState({}, '', `/manage${suffix}`);
      await openManage();
      expect(await page().findByRole('alert')).toHaveTextContent('That sign-in link did not work');
    },
  );

  it('says when the build has no sign-in settings', async () => {
    vi.stubEnv('VITE_SUPABASE_PUBLISHABLE_KEY', '');
    await openManage();
    expect(page().getByText(/VITE_SUPABASE_PUBLISHABLE_KEY/)).toBeInTheDocument();
    expect(page().queryByRole('textbox')).toBeNull();
  });
});

describe('signed in', () => {
  it('shows who is signed in and signs out', async () => {
    api.on(`POST ${AUTH_URL}/auth/v1/logout`, { body: {} });
    const { container } = await openAsOperator();
    expect(page().getByText('operator@example.com')).toBeInTheDocument();
    named(container);
    await userEvent.click(page().getByRole('button', { name: 'Sign out' }));
    expect(await page().findByRole('textbox', { name: 'Email' })).toBeInTheDocument();
    expect(page().queryByRole('button', { name: 'Add app' })).toBeNull();
  });

  it('lists archived apps apart and read-only', async () => {
    await openAsOperator();
    const archived = within(page().getByRole('region', { name: 'Archived apps' }));
    expect(archived.getByRole('link', { name: 'Old App' })).toHaveAttribute('href', '/apps/old');
    expect(archived.queryByRole('button')).toBeNull();
    const live = within(page().getByRole('region', { name: 'Live apps' }));
    expect(live.getByRole('button', { name: 'Archive Groww' })).toBeInTheDocument();
    expect(live.queryByText('Old App')).toBeNull();
  });

  it('test_DSH_05_slots_full', async () => {
    api.apps(...FULL);
    await openAsOperator();
    const add = page().getByRole('button', { name: 'Add app' });
    expect(add).toBeDisabled();
    expect(add).toHaveAccessibleDescription('All 5 slots are used. Archive an app to add another.');
    expect(page().getByText('5 of 5 slots used')).toBeInTheDocument();
    expect(page().getByRole('button', { name: 'Replace App A' })).toBeEnabled();
  });

  it('is offered when there are no apps yet', async () => {
    api.apps();
    const { currentPath } = openRoute('/');
    await userEvent.click(await page().findByRole('button', { name: 'Manage apps' }));
    expect(currentPath()).toBe('/manage');
    expect(await page().findByText('No apps yet')).toBeInTheDocument();
  });

  it('is reachable from the app picker', async () => {
    const { currentPath } = openRoute('/help');
    await userEvent.click(await screen.findByRole('button', { name: /^Choose app/ }));
    await userEvent.click(within(screen.getByRole('banner')).getByRole('link', { name: 'Manage apps' }));
    expect(currentPath()).toBe('/manage');
    expect(within(screen.getByRole('banner')).queryByRole('link', { name: 'Manage apps' })).toBeNull();
  });
});

describe('adding an app', () => {
  beforeEach(async () => {
    api.on('POST /apps', { status: 201, body: REGISTERED });
    await openAsOperator();
    await userEvent.click(page().getByRole('button', { name: 'Add app' }));
  });

  it('test_DSH_06_add_flow', async () => {
    await searchFor('Kite');
    expect(api.sent).toEqual([
      { path: 'POST /search', body: { name: 'Kite', country: 'in' }, authorization: `Bearer ${OPERATOR_TOKEN}` },
    ]);
    expect(store('Google Play').getByText(/Kite by Zerodha Ltd/)).toBeInTheDocument();
    expect(store('Google Play').getByText(/12,34,567/)).toBeInTheDocument();
    dialog().getAllByRole('radio').forEach((radio) => expect(radio).not.toBeChecked());

    const next = dialog().getByRole('button', { name: 'Review' });
    expect(next).toBeDisabled();
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    expect(next).toBeDisabled();
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    await userEvent.click(next);

    expect(dialog().getByText('com.zerodha.kite3')).toBeInTheDocument();
    expect(dialog().getByText('Not on this store')).toBeInTheDocument();
    expect(dialog().getByRole('textbox', { name: 'Display name' })).toHaveValue('Kite');
    expect(api.sent).toHaveLength(1);
    named(screen.getByRole('dialog'));

    api.apps(GROWW, COIN, KITE, OLD);
    await userEvent.click(dialog().getByRole('button', { name: 'Add app' }));
    expect(await screen.findByText('Kite was added. Backfill is queued for the next daily run.')).toBeInTheDocument();
    expect(api.sent[1]).toEqual({
      path: 'POST /apps',
      body: { display_name: 'Kite', play_package_id: 'com.zerodha.kite3', app_store_id: null, country: 'in', lang: 'en' },
      authorization: `Bearer ${OPERATOR_TOKEN}`,
    });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(await page().findByText('3 of 5 slots used')).toBeInTheDocument();
    expect(page().getByRole('link', { name: 'Kite' })).toBeInTheDocument();
  });

  it('never turns the review button into the confirm button', async () => {
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    const review = dialog().getByRole('button', { name: 'Review' });
    await userEvent.click(review);
    const back = dialog().getByRole('button', { name: 'Back' });
    expect(review).not.toBeInTheDocument();
    await userEvent.click(back);
    expect(back).not.toBeInTheDocument();
  });

  it('refuses an app that is on neither store', async () => {
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: 'Not on this store' }));
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    expect(dialog().getByRole('button', { name: 'Review' })).toBeDisabled();
    expect(dialog().getByText('Choose a listing on at least one store.')).toBeInTheDocument();
  });

  it('takes an ID the search did not find', async () => {
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: 'Enter a package name' }));
    await userEvent.type(store('Google Play').getByRole('textbox', { name: 'Package name' }), ' com.other.app ');
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Review' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Add app' }));
    await waitFor(() => expect(api.sent).toHaveLength(2));
    expect(api.sent[1].body).toMatchObject({ play_package_id: 'com.other.app', app_store_id: null });
  });

  it('keeps one store usable when the other fails, and searches again', async () => {
    api.on(
      'POST /search',
      { body: { ...KITE_SEARCH, stores: { ...KITE_SEARCH.stores, play_store: storeSearch('play_store', { status: 'error', message: 'Store search failed. Try again.' }) } } },
      { body: KITE_SEARCH },
    );
    await searchFor('Kite');
    expect(store('Google Play').getByText('Store search failed. Try again.')).toBeInTheDocument();
    await userEvent.click(store('App Store').getByRole('radio', { name: /Zerodha Kite/ }));
    await userEvent.click(store('Google Play').getByRole('button', { name: 'Search again' }));
    expect(await store('Google Play').findByRole('radio', { name: /Kite by Zerodha/ })).toBeInTheDocument();
    expect(store('App Store').getByRole('radio', { name: /Zerodha Kite/ })).toBeChecked();
  });

  it.each([
    [{ rating_count: null }, '4.4★'],
    [{ rating: null, rating_count: null }, 'No rating'],
  ])('shows only the rating facts a store gave: %j', async (facts, text) => {
    const found = { ...candidate('play_store', 'com.zerodha.kite3', 'Kite by Zerodha'), ...facts };
    api.on('POST /search', {
      body: { ...KITE_SEARCH, stores: { ...KITE_SEARCH.stores, play_store: storeSearch('play_store', { candidates: [found] }) } },
    });
    await searchFor('Kite');
    expect(store('Google Play').getByText(text)).toBeInTheDocument();
  });

  it('drops a choice that a new search no longer lists', async () => {
    const without = { ...KITE_SEARCH.stores, play_store: storeSearch('play_store', { status: 'error', message: 'Store search failed. Try again.' }) };
    const emptied = { ...KITE_SEARCH.stores, app_store: storeSearch('app_store', { status: 'empty' }) };
    api.on('POST /search', { body: { ...KITE_SEARCH, stores: without } }, { body: { ...KITE_SEARCH, stores: emptied } });
    await searchFor('Kite');
    await userEvent.click(store('App Store').getByRole('radio', { name: /Zerodha Kite/ }));
    await userEvent.click(store('Google Play').getByRole('button', { name: 'Search again' }));
    await userEvent.click(await store('Google Play').findByRole('radio', { name: /Kite by Zerodha/ }));
    expect(dialog().getByRole('button', { name: 'Review' })).toBeDisabled();
  });

  it('keeps a choice made while searching again', async () => {
    const without = { ...KITE_SEARCH.stores, play_store: storeSearch('play_store', { status: 'error', message: 'Store search failed. Try again.' }) };
    let finish = () => {};
    api.on('POST /search', { body: { ...KITE_SEARCH, stores: without } }, {
      body: KITE_SEARCH,
      after: new Promise<void>((resolve) => { finish = resolve; }),
    });
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('button', { name: 'Search again' }));
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    finish();
    await store('Google Play').findByRole('radio', { name: /Kite by Zerodha/ });
    expect(store('App Store').getByRole('radio', { name: 'Not on this store' })).toBeChecked();
  });

  it('forgets a refusal and keeps the typed name when going back', async () => {
    api.on('POST /apps', { status: 409, body: { error: 'com.zerodha.kite3 already belongs to Groww (groww).' } });
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Review' }));
    await userEvent.type(dialog().getByRole('textbox', { name: 'Display name' }), ' Pro');
    await userEvent.click(dialog().getByRole('button', { name: 'Add app' }));
    await dialog().findByRole('alert');
    await userEvent.click(dialog().getByRole('button', { name: 'Back' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Review' }));
    expect(dialog().queryByRole('alert')).toBeNull();
    expect(dialog().getByRole('textbox', { name: 'Display name' })).toHaveValue('Kite Pro');
  });

  it('says when neither store has a match', async () => {
    api.on('POST /search', {
      body: {
        ...KITE_SEARCH,
        no_matches: true,
        stores: {
          play_store: storeSearch('play_store', { status: 'empty', message: 'Not found on this store.' }),
          app_store: storeSearch('app_store', { status: 'empty', message: 'Not found on this store.' }),
        },
      },
    });
    await searchFor('Nothing');
    expect(dialog().getByText(/No matches on either store/)).toBeInTheDocument();
  });

  it.each([
    [{ status: 409, body: { error: 'com.zerodha.kite3 already belongs to Groww (groww).' } }, 'already belongs to Groww'],
    [{ status: 401, body: { error: 'Session is invalid or expired. Sign in again.' } }, 'Sign in again'],
    [{ status: 403, body: { error: 'This account is not an operator.' } }, 'not an operator'],
    [{ status: 503, body: { error: 'Operator sign-in is not configured on this backend.' } }, 'not configured on this backend'],
    ['offline' as const, 'may still have been saved'],
  ])('reports a refused registration once and never repeats it: %j', async (answer, message) => {
    api.on('POST /apps', answer);
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    await userEvent.click(store('App Store').getByRole('radio', { name: /Zerodha Kite/ }));
    await userEvent.click(dialog().getByRole('button', { name: 'Review' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Add app' }));
    expect(await dialog().findByRole('alert')).toHaveTextContent(message);
    expect(api.sent.filter((s) => s.path === 'POST /apps')).toHaveLength(1);
    expect(dialog().getByRole('textbox', { name: 'Display name' })).toHaveValue('Kite');
  });

  it('test_UIC_08_dialog_error_heading_sits_under_the_dialog_title', async () => {
    api.on('POST /apps', { status: 409, body: { error: 'com.zerodha.kite3 already belongs to Groww (groww).' } });
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    await userEvent.click(store('App Store').getByRole('radio', { name: /Zerodha Kite/ }));
    await userEvent.click(dialog().getByRole('button', { name: 'Review' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Add app' }));
    const alert = within(await dialog().findByRole('alert'));
    const title = dialog().getAllByRole('heading')[0];
    const levelOf = (heading: HTMLElement) => Number(heading.tagName.slice(1));
    expect(levelOf(alert.getByRole('heading'))).toBe(levelOf(title) + 1);
  });

  it('keeps the choices when going back', async () => {
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Review' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Back' }));
    expect(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ })).toBeChecked();
  });

  it('clears the choices for a new search', async () => {
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    await userEvent.type(dialog().getByRole('textbox', { name: 'App name' }), ' two');
    await userEvent.click(dialog().getByRole('button', { name: 'Search stores' }));
    await waitFor(() => expect(api.sent).toHaveLength(2));
    await waitFor(() => dialog().getAllByRole('radio').forEach((radio) => expect(radio).not.toBeChecked()));
  });

  it('registers nothing when it is cancelled', async () => {
    await searchFor('Kite');
    await userEvent.click(dialog().getByRole('button', { name: 'Cancel' }));
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(api.sent.map((s) => s.path)).toEqual(['POST /search']);
  });
});

describe('changing an app', () => {
  beforeEach(openAsOperator);

  it('renames', async () => {
    api.on('PATCH /apps/groww', { body: { ...GROWW, display_name: 'Groww App' } });
    await userEvent.click(page().getByRole('button', { name: 'Rename Groww' }));
    const name = dialog().getByRole('textbox', { name: 'Display name' });
    expect(dialog().getByRole('button', { name: 'Save name' })).toBeDisabled();
    await userEvent.type(name, ' App');
    api.apps({ ...GROWW, display_name: 'Groww App' }, COIN, OLD);
    await userEvent.keyboard('{Enter}');
    expect(await screen.findByText('Groww is now called Groww App.')).toBeInTheDocument();
    expect(api.sent).toEqual([
      { path: 'PATCH /apps/groww', body: { display_name: 'Groww App' }, authorization: `Bearer ${OPERATOR_TOKEN}` },
    ]);
    expect(await page().findByRole('link', { name: 'Groww App' })).toBeInTheDocument();
  });

  it('test_DSH_07_archive_confirm', async () => {
    api.on('DELETE /apps/zerodha-coin', { body: { ...COIN, status: 'archived' } });
    await userEvent.click(page().getByRole('button', { name: 'Archive Zerodha Coin' }));
    expect(screen.getByRole('dialog', { name: 'Archive Zerodha Coin?' })).toBeInTheDocument();
    expect(api.sent).toEqual([]);
    named(screen.getByRole('dialog'));
    api.apps(GROWW, app('zerodha-coin', 'Zerodha Coin', 'archived'), OLD);
    await userEvent.click(dialog().getByRole('button', { name: 'Archive Zerodha Coin' }));
    expect(await screen.findByText('Zerodha Coin was archived.')).toBeInTheDocument();
    expect(await page().findByText('1 of 5 slots used')).toBeInTheDocument();
    expect(api.sent).toEqual([
      { path: 'DELETE /apps/zerodha-coin', body: null, authorization: `Bearer ${OPERATOR_TOKEN}` },
    ]);
  });

  it('archives nothing when it is cancelled', async () => {
    await userEvent.click(page().getByRole('button', { name: 'Archive Groww' }));
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(api.sent).toEqual([]);
  });

  it('cannot be closed while it is saving', async () => {
    api.on('DELETE /apps/groww', 'never');
    await userEvent.click(page().getByRole('button', { name: 'Archive Groww' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Archive Groww' }));
    await userEvent.keyboard('{Escape}');
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(dialog().getByRole('button', { name: 'Archive Groww' })).toBeDisabled();
  });

  it('replaces in the same slot', async () => {
    api.on('POST /apps/groww/replace', { status: 201, body: { ...REGISTERED, slots_used: 2 } });
    await userEvent.click(page().getByRole('button', { name: 'Replace Groww' }));
    expect(dialog().getByText(/Groww is archived/)).toBeInTheDocument();
    await searchFor('Kite');
    await userEvent.click(store('Google Play').getByRole('radio', { name: /Kite by Zerodha/ }));
    await userEvent.click(store('App Store').getByRole('radio', { name: 'Not on this store' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Review' }));
    await userEvent.click(dialog().getByRole('button', { name: 'Replace Groww' }));
    expect(await screen.findByText('Kite replaced Groww. Backfill is queued for the next daily run.')).toBeInTheDocument();
    expect(api.sent[1]).toMatchObject({ path: 'POST /apps/groww/replace', body: { play_package_id: 'com.zerodha.kite3' } });
  });

  it('keeps the list on screen while it reloads', async () => {
    api.on('PATCH /apps/groww', { body: { ...GROWW, display_name: 'Groww 2' } });
    await userEvent.click(page().getByRole('button', { name: 'Rename Groww' }));
    await userEvent.type(dialog().getByRole('textbox', { name: 'Display name' }), ' 2');
    api.on('/apps?include_archived=true', 'never');
    await userEvent.click(dialog().getByRole('button', { name: 'Save name' }));
    await screen.findByText('Groww is now called Groww 2.');
    expect(page().getByRole('link', { name: 'Zerodha Coin' })).toBeInTheDocument();
    expect(page().queryByRole('status', { name: 'Loading' })).toBeNull();
  });
});
