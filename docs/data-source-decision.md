# ADR-7 & ADR-8: Play Store Data Source Decision & Import Contract

**Status:** Approved  
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
