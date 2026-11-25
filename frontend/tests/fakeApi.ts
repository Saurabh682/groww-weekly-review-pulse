import { vi } from 'vitest';
import { AppHealth, AppRecord, AppStatus, CollectionRun, PulseHistory, PulseWeek, PulseWeekDetail, StoreCandidate, StoreSearch } from '../src/data/types';

export const API_URL = 'http://api.test';
export const AUTH_URL = 'http://auth.test';
export const OPERATOR_TOKEN = 'operator-token';
const SESSION_KEY = 'sb-auth-auth-token';
const A_DAY = 86_400;

export interface SentRequest {
  path: string;
  body: unknown;
  authorization: string | null;
}

type Answer = { status?: number; body?: unknown; contentType?: string; after?: Promise<void> } | 'offline' | 'never';

export function app(key: string, name: string, status: AppStatus = 'active', more: Partial<AppRecord> = {}): AppRecord {
  return {
    app_key: key,
    display_name: name,
    status,
    play_package_id: `com.${key}`,
    app_store_id: '1',
    country: 'in',
    lang: 'en',
    category: 'Finance',
    created_at: '2026-11-23T00:00:00+00:00',
    archived_at: status === 'archived' ? '2026-11-24T10:27:37+00:00' : null,
    ...more,
  };
}

export function pulse(week: string, shares: Record<string, number>, more: Partial<PulseWeek> = {}): PulseWeek {
  return {
    week_start: week,
    status: 'published',
    window_start: '2026-08-31',
    window_end: '2026-11-22',
    total_reviews: 4736,
    analyzed_reviews: 1888,
    avg_rating: 2.89,
    coverage_weeks: 12,
    short_coverage: false,
    doc_url: `https://docs.google.com/document/d/${week}/edit`,
    draft_created: true,
    published_at: '2026-11-24T13:36:11+00:00',
    themes: Object.entries(shares).map(([label, share], i) => ({
      label,
      review_count: Math.round(share * 1888),
      share_pct: share,
      avg_rating: 2.5,
      is_top3: i < 3,
    })),
    ...more,
  };
}

export function run(more: Partial<CollectionRun> = {}): CollectionRun {
  return {
    platform: 'play_store',
    mode: 'daily',
    status: 'ok',
    window_start: '2026-11-22',
    window_end: '2026-11-24',
    covered_start: '2026-11-22',
    fetched: 200,
    inserted: 13,
    source_limit_hit: false,
    feed_gaps: 0,
    error: null,
    started_at: '2026-11-24T10:25:00+00:00',
    finished_at: '2026-11-24T10:25:51+00:00',
    ...more,
  };
}

export function health(of: AppRecord, more: Partial<AppHealth> = {}): AppHealth {
  return {
    app: of,
    collections: { play_store: run(), app_store: null },
    runs: [run()],
    stores: [{ platform: 'play_store', reviews: 4536, caveat: null }],
    ...more,
  };
}

export function history(of: AppRecord, pulses: PulseWeek[], more: Partial<PulseHistory> = {}): PulseHistory {
  return { app_key: of.app_key, pulses, latest_run: null, ...more };
}

export function detail(appKey: string, week: PulseWeek): PulseWeekDetail {
  return {
    ...week,
    app_key: appKey,
    stores: [{ platform: 'play_store', reviews: 4536, caveat: null }],
    note_markdown: null,
  };
}

export function candidate(platform: StoreCandidate['platform'], id: string, title: string): StoreCandidate {
  return {
    platform,
    listing_id: id,
    title,
    developer: `${title} Ltd`,
    icon_url: null,
    rating: 4.4,
    rating_count: 1234567,
    category: 'Finance',
    matched_by: 'search',
  };
}

export function storeSearch(platform: StoreSearch['platform'], more: Partial<StoreSearch> = {}): StoreSearch {
  return { platform, status: 'ok', candidates: [], message: null, ...more };
}

export function signIn(): void {
  const now = Math.floor(Date.now() / 1000);
  localStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      access_token: OPERATOR_TOKEN,
      refresh_token: 'refresh',
      token_type: 'bearer',
      expires_in: A_DAY,
      expires_at: now + A_DAY,
      user: { id: 'u1', aud: 'authenticated', email: 'operator@example.com', app_metadata: {}, user_metadata: {}, created_at: '' },
    }),
  );
}

export class FakeApi {
  readonly sent: SentRequest[] = [];
  readonly answers = new Map<string, Answer[]>();
  readonly calls: string[] = [];

  on(path: string, ...answers: Answer[]): this {
    this.answers.set(path, answers);
    return this;
  }

  apps(...apps: AppRecord[]): this {
    const live = apps.filter((a) => a.status !== 'archived').length;
    return this.on('/apps?include_archived=true', { body: { slots_used: live, slots_total: 5, apps } });
  }

  shows(of: AppRecord, pulses: PulseWeek[], more: Partial<AppHealth> = {}): this {
    this.on(`/apps/${of.app_key}/pulses?limit=12`, { body: history(of, pulses) });
    pulses.forEach((p) => this.on(`/apps/${of.app_key}/pulses/${p.week_start}`, { body: detail(of.app_key, p) }));
    return this.on(`/apps/${of.app_key}/health`, { body: health(of, more) });
  }

  install(): this {
    vi.stubEnv('VITE_API_URL', API_URL);
    vi.stubEnv('VITE_SUPABASE_URL', AUTH_URL);
    vi.stubEnv('VITE_SUPABASE_PUBLISHABLE_KEY', 'sb_publishable_test');
    vi.stubGlobal('fetch', (input: RequestInfo | URL, init: RequestInit = {}) => this.answer(String(input), init));
    return this;
  }

  private answer(url: string, init: RequestInit): Promise<Response> {
    const method = init.method ?? 'GET';
    const route = url.startsWith(API_URL) ? url.slice(API_URL.length) : url.split('?')[0];
    const path = method === 'GET' ? route : `${method} ${route}`;
    this.calls.push(path);
    if (method !== 'GET') {
      this.sent.push({
        path,
        body: init.body ? JSON.parse(String(init.body)) : null,
        authorization: new Headers(init.headers).get('authorization'),
      });
    }
    const queue = this.answers.get(path) ?? [{ status: 404, body: { error: `Unknown: ${path}` } }];
    const next = queue.length > 1 ? queue.shift()! : queue[0];
    if (next === 'offline') return Promise.reject(new TypeError('Failed to fetch'));
    if (next === 'never') {
      return new Promise((_, reject) => init.signal?.addEventListener('abort', () => reject(init.signal?.reason)));
    }
    return (next.after ?? Promise.resolve()).then(
      () => new Response(JSON.stringify(next.body ?? {}), {
        status: next.status ?? 200,
        headers: { 'content-type': next.contentType ?? 'application/json' },
      }),
    );
  }
}
