# ADR-7 & ADR-8: Play Store Data Source Decision & Import Contract

**Status:** Superseded by ADR-9 and ADR-10 (§5, §6) on 2026-11-23. §1-§4 are kept as the v1 record. The field allowlist (§3) and the identity exclusion rule still apply to every source.  
**Date:** 2026-11-11  
**Decision Owner:** Engineering / AG Team  

---

## 1. Context & Constraints

The Groww Weekly Review Pulse requires ingesting public reviews over an 8–12 week window to cluster user sentiment and produce a concise weekly pulse.
Key constraints:
1. **Public Exports Only**: No scraping behind user/store logins, and no ToS-violating automation.
2. **Apple App Store Excluded**: As decided, Apple App Store is deferred for initial phases to simplify ingestion (`ING-15`).
3. **No Reviewer PII**: No usernames, profile IDs, avatars, or device IDs must ever enter the pipeline or data store (`ING-01`).

---

## 2. Ingestion Decision

* **Primary Mode:** **`csv_import`** (Manual or permitted public export).
* Public reviews exported from Google Play Store are placed in `data/imports/play_reviews.csv`.
* **Automated Collection Guard:** Any automated collection module remains **strictly disabled by default** (`allow_automated: false`). If an automated collector is ever invoked without formal approval and feature flag enablement, the pipeline immediately aborts with a clear error (`ING-14`, `SEC-05`).

---

## 3. Review Import Contract

The ingestion adapter enforces a strict **field allowlist**. Source files may contain arbitrary headers, but only the following fields are parsed into the normalized data model:

| Field | Type | Required | Description / Rules |
| :--- | :--- | :--- | :--- |
| `rating` | `int` | Yes | Rating integer between 1 and 5 (`ING-05`) |
| `text` | `string` | Yes | Raw review content; normalized and scrubbed in subsequent stages |
| `date` | `string` / `date` | Yes | Review publication date (ISO or standard format) |
| `title` | `string` | No | Optional review title (Play Store reviews often omit title) (`ING-04`) |
| `app_version` | `string` | No | App version string (e.g. `12.4.1`) |

### Identity Exclusion Rule (`ING-01`)
Any columns associated with reviewer identity—such as `author_name`, `author_email`, `user_id`, `avatar_url`, or `device_id`—are **dropped immediately at the ingestion boundary**. They are never read into memory models, never persisted to SQLite, and never copied to `data/raw/`.

---

## 4. Known Limits

- **Window Depth:** Google Play public feeds and standard exports typically surface the most recent reviews (approx. 8–12 weeks). If a low-volume period provides fewer reviews, the pipeline will flag low sample size rather than failing.
- **Language Coverage:** Reviews in India contain a mix of English, Hindi, and Hinglish. Language detection will tag these reviews; non-English reviews are eligible for theme clustering but ineligible for verbatim quotes by default.

---

## 5. ADR-9: Automated Collection From Both Stores (v2)

**Status:** Approved  
**Date:** 2026-11-23  
**Supersedes:** ADR-7 (CSV import as default), ADR-8 (Play Store only)

### Context
v2 registers up to 5 apps by name and must collect their reviews on a schedule with no manual export. Manual CSV import cannot scale to 5 apps on a daily cadence, and the App Store must be included.

### Decision

| Store | Method | Access | Limits |
|---|---|---|---|
| **App Store** | Apple customer-reviews RSS feed, JSON: `https://itunes.apple.com/{country}/rss/customerreviews/page={1..10}/id={app_store_id}/sortby=mostrecent/json` | Public feed published by Apple; no login, no key | 50 reviews per page, 10 pages, about 500 most recent reviews per country per fetch |
| **Play Store** | `google-play-scraper` `reviews()` with `Sort.NEWEST` and continuation tokens | Public listing data; no login, no key; not an official Google API | No documented cap; requests rate-limited by us (≥1 s between pages); library may break when Google changes the page |
| **Search (App Store)** | iTunes Search API `https://itunes.apple.com/search?term=...&country=...&entity=software&limit=3`, verify with `https://itunes.apple.com/lookup?id=...` | Public, official | Apple asks for about 20 calls per minute at most |
| **Search (Play Store)** | `google-play-scraper` `search()`, verify with `app()` | Same as Play reviews | Same as Play reviews |

### Rules
1. The field allowlist in §3 applies to both stores. Mapping:
   - App Store: `im:rating` → `rating`, `title.label` → `title`, `content.label` → `text`, `updated.label` → `date`, `im:version.label` → `app_version`.
   - Play Store: `score` → `rating`, `content` → `text`, `at` → `date`, `reviewCreatedVersion` → `app_version`; no title.
2. Dropped at extraction for both stores: author name, author URI, avatar, the store's review ID, `thumbsUpCount`, developer replies (`replyContent`, `repliedAt`).
3. No collector ever sends credentials, cookies or a logged-in session.
4. Each store has a kill switch: `sources.play_store.enabled` and `sources.app_store.enabled`. When off, collection for that store is skipped and the run records `skipped_disabled`.
5. The v1 `allow_automated` flag and its guard (`ING-14`, `SEC-05`) are retired. They are replaced by `COL-01` (identity fields never extracted) and `COL-02` (disabled store makes zero network calls) in `edge-case.md`.
6. CSV import (`csv_import`) stays available as a manual path for one app, for testing and recovery.

### Risks Accepted
- `google-play-scraper` is unofficial. It reads public pages without login and at low volume, which keeps this within the "public, login-free" constraint, but Google can change its pages at any time. Mitigation: daily collection failures surface on the dashboard; CSV import remains as a fallback.
- The App Store cap means a backfill for a busy app may cover less than 12 weeks. Mitigation: daily collection keeps new reviews inside the cap; short coverage is recorded (`source_limit_hit`) and shown in the note header and dashboard.

### Observed 2026-11-23: RSS feed returns empty pages
During the Phase 8 live run the customer-reviews feed returned HTTP 200 with no review entries for Groww (`id=1404871703`, `in`) and for other apps, in both JSON and XML. Earlier the same day single pages (3 in JSON, 6 in XML) held 50 reviews while the rest were empty; pages 1-2, which hold the newest reviews, stayed empty on every retry. Several 2026 developer reports describe the same behaviour. The collector therefore sweeps all 10 pages, tries XML when JSON is empty, counts empty pages as `feed_gaps`, and marks the run partial (`COL-13`), so a gap never reads as "zero reviews".

**Open decision (owner: operator):** whether to keep RSS as the only App Store source and accept gaps, or approve a different source. The App Store website's own review endpoint is undocumented, needs a token taken from the web page, and is outside the "public, documented, login-free" rule above, so it is not used without a new ADR.

---

## 6. ADR-10: Collection Cadence (v2)

**Status:** Approved  
**Date:** 2026-11-23

### Context
The operator asked for a monthly collection on the 1st plus a collection of older reviews when an app is added. A weekly pulse fed by monthly collection would have no new reviews for 3 of every 4 weeks, and the App Store 500-review cap loses reviews for busy apps over a month.

### Decision

| Mode | When | Window per app and store |
|---|---|---|
| Backfill | On demand, right after an app is confirmed | Last 12 weeks, then generate the first pulse |
| Daily | 20:30 UTC every day | Last 3 days (overlap absorbs late-indexed reviews) |
| Reconcile | 21:30 UTC on the 1st | Previous calendar month |
| Weekly pulse | 03:30 UTC Monday | Uses stored reviews; no collection |

Daily collection also keeps the Supabase free-tier project active; Supabase pauses free projects after a week without activity.

### Consequences
- About 30 short collection runs per app per month on GitHub Actions. With 5 apps this stays well inside the free Actions minutes.
- Dedupe makes all overlapping windows safe.
