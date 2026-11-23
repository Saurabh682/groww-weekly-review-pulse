# Problem Statement: Weekly Review Pulse (Multi-App)

> Turn raw app-store feedback for **up to 5 apps** into a one-page weekly pulse per app that a team can scan in minutes: what users care about, what they actually said, and what to do next.

**Version:** v2 (multi-app), 2026-11-23. Supersedes v1, which covered Groww on Google Play only. v1 is kept in git history (`c4227a6`). Groww (`com.nextbillion.groww`) stays as the first registered app.

---

## 1. Overview

Apps receive a constant stream of public reviews on the Google Play Store and the Apple App Store. These reviews carry signal about bugs, onboarding friction, payment failures, performance and UX, but are too many and too unstructured for Product, Support and Leadership to read directly.

The system:

1. Lets an operator register **up to 5 apps** by name. The system searches both stores, shows the top matches, and the operator confirms the correct listing on each store (or marks "not on this store").
2. Collects public reviews for every registered app on a schedule (GitHub Actions, one matrix workflow), starting with a **12-week backfill** as soon as an app is confirmed.
3. Cleans and anonymizes reviews, and clusters each app's reviews into **at most 5 themes**.
4. Produces a **one-page weekly note per app** (≤250 words) with top themes, verbatim quotes and action ideas.
5. Publishes each app's note to **its own Google Doc** and creates **its own Gmail draft**, both through **MCP (Composio)**.
6. Shows a **dashboard** where the operator picks an app and sees its latest pulse, theme trends, collection health and links to its Doc and draft.

Apps can be renamed, replaced or removed later. Removing an app frees its slot and keeps its history.

---

## 2. Goals and Non-Goals

### Goals
- A fast, trustworthy, scannable weekly health check per app.
- Adding an app takes one name and one confirmation; no store IDs typed by hand.
- Every claim grounded in real reviews: quotes verbatim, themes traceable to counts.
- Concrete, theme-linked action ideas per app.
- MCP-first delivery so auth and HTTP plumbing are not reinvented.
- No PII in any artifact.

### Non-Goals
- More than 5 active apps.
- Real-time monitoring or alerting.
- Replying to reviews on the stores.
- Sending email. Drafts only.
- Scraping behind store logins or any collection that needs an account.
- Handling Google credentials or writing a Google OAuth/REST client.

---

## 3. Audience and Value

| Audience | What they get |
|---|---|
| **Operator** | One place to register apps, watch collection health and open each pulse |
| **Product / Growth** | Prioritized fixes per app, backed by real user signals |
| **Support** | Messaging aligned with what users say; early view of recurring complaints |
| **Leadership** | One page per app, plus a dashboard to switch between apps |

---

## 4. End-to-End Flow ("What Done Looks Like")

```
[Operator types app name] -> [Search Play + App Store] -> [Operator confirms listings] -> [App registered (slot n/5)]
                                                                                              |
                                                                                    [12-week backfill job]
                                                                                              |
[Daily collect] --> [Supabase: reviews per app] <-- [Monthly reconcile]                       |
                                  |                                                           |
                       [Weekly pulse job, Monday, per app (matrix)] <-------------------------+
                                  |
      [clean + anonymize] -> [themes (<=5)] -> [note (<=250 words)] -> [validation gate]
                                                                              |
                                          +-----------------------------------+--------------------+
                                          v                                                        v
                             [Google Doc per app via Composio MCP]                 [Gmail draft per app via Composio MCP]
                                          |
                                 [Dashboard: pick app -> latest pulse, trends, health]
```

**Definition of done:** an operator adds an app by name, confirms its listings, and without further manual steps that app gets (a) a 12-week backfill, (b) a first pulse as a Google Doc and a Gmail draft, (c) a new pulse every Monday, and (d) a dashboard view, with no PII anywhere.

---

## 5. Functional Requirements

### 5.1 App Registry
- Holds at most **5 active apps**. The 6th add is rejected with a clear message. The cap is enforced in the database, not only in the UI.
- Each app has an immutable internal `app_key` (slug, e.g. `groww`), a display name, a country (default `in`), a language (default `en`), and a store listing for Play and/or App Store. At least one store listing is required.
- **Rename** changes only the display name. History, Docs and drafts keep working.
- **Replace** (pointing an app at different store listings) is not an edit: it archives the old app and creates a new one, so one app's history never mixes two listings.
- **Remove** archives the app: its slot is freed, its schedule stops, and its history and Docs stay readable in the dashboard.
- Adding a store listing that is already registered to an active app is rejected.
- Only an authenticated operator can add, rename, replace or remove apps.

### 5.2 App Resolution (name → store listings)
- Given a name, search both stores in the app's country and return the **top 3 matches per store** with icon, title, developer, rating and rating count.
- **App Store:** Apple's public iTunes Search API (`itunes.apple.com/search`, `entity=software`).
- **Play Store:** the `google-play-scraper` search function (public listing data, no login).
- The operator confirms one match per store or picks "not on this store". Nothing is registered until confirmed.
- After confirmation, the system re-fetches each listing by ID to verify it exists, and stores its category (used as theming context).
- If one store's search fails or times out, the operator can confirm the other store now and add the missing store later.

### 5.3 Review Collection
- Collection is automated for both stores. This reverses the v1 decision; see ADR-9 in `data-source-decision.md`.
- **App Store:** Apple's public customer-reviews RSS feed (JSON), most recent first, 10 pages of 50 reviews per country. One fetch is capped at about 500 reviews.
- **Play Store:** `google-play-scraper` `reviews()` sorted by newest with continuation tokens, rate-limited.
- Field allowlist at the boundary: `rating`, `title`, `text`, `date`, `app_version`. Reviewer name, avatar, user ID, the store's review ID and developer replies are dropped at extraction and never stored.
- Modes:

| Mode | Trigger | Window | Purpose |
|---|---|---|---|
| **Backfill** | App confirmed (on demand) | Last 12 weeks | Seed a new app, then generate its first pulse |
| **Daily** | Every day | Last 3 days | Keep data fresh; stay under the App Store 500-review cap |
| **Reconcile** | Monthly, after the month closes | Previous calendar month | Re-sweep the month and catch late or edited reviews |

- All modes upsert with the existing dedupe key, so overlapping windows add no duplicates.
- When a fetch hits a source limit (App Store page 10 reached before the window start), the collection run records `source_limit_hit` and the dashboard shows the window actually covered.

### 5.4 Cleaning and Privacy Scrubbing
Unchanged from v1 and applied to every app: drop identity fields, scrub embedded PII (phones, emails, PAN/Aadhaar-like, UPI IDs, account/order IDs, sign-off names), normalize text, detect language, filter spam and low-info reviews from clustering.

### 5.5 Theme Clustering
- At most **5 themes per app per run**, including "Other".
- Themes are derived from each app's own reviews. Prompts receive the app's display name and store category; prompt files contain no hardcoded app names or app-specific theme lists.
- Each theme has a label, a one-line description, review count, share and average rating.

### 5.6 Weekly One-Page Note (per app)
Unchanged contract: ≤250 words, top 3 themes, exactly 3 verbatim quotes, exactly 3 action ideas, and a header with app name, window and review count. If one store's coverage is short (source limit or no listing), the header says which stores were included.

### 5.7 Google Docs Delivery (Composio MCP)
- One Doc per app per week, titled `<App> Weekly Review Pulse: Week of YYYY-MM-DD`.
- Re-running the same app and week updates that Doc in place; it never creates a second one.

### 5.8 Gmail Draft (Composio MCP)
- One draft per app per week, addressed to the configured recipient, subject `<App> Weekly Review Pulse | Week of YYYY-MM-DD`, body with the note and the Doc link.
- Re-running updates the same draft. The system never sends email; send tools are blocked in the MCP capability map.

### 5.9 Scheduling (GitHub Actions)
- **One workflow file** with a matrix over active apps. The app list is read from the registry at run time, so adding or removing an app never edits workflow files.
- Schedules (cron is UTC; IST shown for reference):

| Job | Cron (UTC) | IST |
|---|---|---|
| Daily collect | `30 20 * * *` | 02:00 daily |
| Weekly pulse | `30 3 * * 1` | 09:00 Monday |
| Monthly reconcile | `30 21 1 * *` | 03:00 on the 2nd, covering the previous month |

- **Backfill** runs through `workflow_dispatch` with an `app_key` input. The backend triggers it right after an app is confirmed. If the trigger fails, the next daily run backfills any app still marked `pending_backfill`.
- One failing app never fails the other apps' matrix jobs. Runs for the same app never overlap.

### 5.10 Dashboard
- App switcher listing the active apps, with an "archived" toggle.
- Per app: latest pulse, theme table, theme share trend across weeks, links to the Doc and draft, collection health (last run, reviews per store, covered window, source-limit flags) and run history.
- Manage Apps page: slot counter (n/5), add flow with search and confirmation, rename, replace, archive.

---

## 6. Integration Requirements: MCP First (Composio)

- Google Docs and Gmail go through **Composio's MCP server**. Google auth lives in Composio connected accounts; the pipeline holds only a Composio API key and the connected-account IDs.
- Tools used: `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN`, `GOOGLEDOCS_GET_DOCUMENT_BY_ID`, `GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT`, `GOOGLEDOCS_UPDATE_DOCUMENT_SECTION_MARKDOWN`, `GMAIL_CREATE_EMAIL_DRAFT`, `GMAIL_UPDATE_DRAFT`.
- Blocked tools: `GMAIL_SEND_EMAIL`, `GMAIL_SEND_DRAFT`, and any other send tool.
- Failures: retry with backoff, clear error, local Markdown fallback (unchanged from v1).

---

## 7. Constraints

| Constraint | Requirement |
|---|---|
| **Apps** | At most 5 active apps |
| **Data source** | Public, login-free store data only; identity fields dropped at extraction |
| **Time window** | 12-week window per pulse; App Store backfill may be shorter and must be reported |
| **Themes** | ≤5 per app per run; note shows top 3 |
| **Length** | ≤250 words per note |
| **Quotes** | Exactly 3, verbatim, never fabricated |
| **Actions** | Exactly 3, theme-grounded |
| **Privacy** | No PII in any artifact: database, Docs, drafts, logs, Actions logs, dashboard, screenshots |
| **Credentials** | No Google credentials in the pipeline; all secrets in GitHub/HF secret stores, never in the repo |
| **Delivery** | Drafts only, never send |

---

## 8. Data Model (Summary)

Full schema in `multi-app-architecture.md` §5.

| Entity | Key fields |
|---|---|
| `apps` | `app_key`, `display_name`, `play_package_id`, `app_store_id`, `country`, `lang`, `category`, `status` (`pending_backfill` / `backfilling` / `active` / `archived` / `failed`), `created_at`, `archived_at` |
| `reviews` | `app_key`, `review_id`, `platform`, `rating`, `title`, `text`, `review_date`, `app_version`, flags |
| `collection_runs` | `app_key`, `platform`, `mode`, window, fetched, inserted, `source_limit_hit`, status |
| `runs`, `themes`, `review_themes` | As v1, plus `app_key` |
| `publish_state` | `(app_key, week_start)` → `doc_id`, `doc_url`, `draft_id`, `content_hash` |

---

## 9. Weekly Note Template

```markdown
# <App> Weekly Review Pulse | Week of <YYYY-MM-DD>
Window: <start> to <end> | Reviews analyzed: <N> (Play <p>, App Store <a>) | Avg rating: <x.x>

## Top 3 Themes
1. **<Theme A>** (<xx%>, avg <x.x>★): <one-line summary>
2. **<Theme B>** (<xx%>, avg <x.x>★): <one-line summary>
3. **<Theme C>** (<xx%>, avg <x.x>★): <one-line summary>

## What Users Said
- "<verbatim quote 1>"
- "<verbatim quote 2>"
- "<verbatim quote 3>"

## Action Ideas
1. **<Theme A>:** <specific next step, owner, intended outcome>
2. **<Theme B>:** <specific next step, owner, intended outcome>
3. **<Theme C>:** <specific next step, owner, intended outcome>
```

---

## 10. Quality Rules for the Note

Unchanged from v1: traceable, verbatim quotes, diverse quotes, actionable, balanced, no overreach, concise.

---

## 11. Acceptance Criteria

- [ ] An app can be added by name; top 3 matches per store are shown; nothing registers without confirmation.
- [ ] A 6th active app is rejected by the database.
- [ ] Rename keeps history; replace archives and creates a new app; remove archives and frees the slot.
- [ ] Confirming an app triggers a 12-week backfill and a first pulse with no manual step.
- [ ] Daily, weekly and monthly jobs run from **one** workflow file with a matrix over active apps.
- [ ] One app's failure does not fail other apps' jobs.
- [ ] Each app's note: ≤5 themes clustered, top 3 shown, 3 verbatim quotes, 3 actions, ≤250 words.
- [ ] Each app gets its own Google Doc and Gmail draft via Composio MCP; reruns update in place.
- [ ] No send tool is callable.
- [ ] The dashboard switches between apps and shows latest pulse, trends, links and collection health.
- [ ] A PII check on the database, Docs, drafts, logs and dashboard finds nothing.
- [ ] No secrets in the repository.
- [ ] README documents setup, sources and their limits, Composio setup, secrets, and how to run each job locally.

---

## 12. Edge Cases to Handle

All v1 cases still apply per app. New cases, with IDs, are in `edge-case.md` §19-§28:

- A name matches several apps, none, or only one store.
- The same listing registered twice; a 6th app; adding while another app is backfilling.
- An app delisted or renamed on the store after registration.
- App Store backfill shorter than 12 weeks (500-review cap).
- A new app with almost no reviews.
- Backfill dispatch fails; a scheduled run overlaps a backfill for the same app.
- Composio connection expired for Docs or Gmail; wrong connected account selected.
- The operator archives an app while its job is running.

---

## 13. Open Questions

- Draft recipient: one address for all apps, or per app? Default: one address.
- Operator sign-in for the Manage Apps page. Default: Supabase Auth magic link, one allowed email.
- Should archived apps ever be hard-deleted? Default: no; out of scope.

---

## 14. Glossary

- **MCP:** Model Context Protocol, a standard for exposing tools to an agent or app.
- **Composio:** hosted tool platform that exposes Gmail and Google Docs as MCP tools and holds the Google auth.
- **Pulse:** the one-page weekly note for one app.
- **Slot:** one of the 5 active-app places in the registry.
- **Backfill / Daily / Reconcile:** the three collection modes in §5.3.
- **PII:** personally identifiable information.
