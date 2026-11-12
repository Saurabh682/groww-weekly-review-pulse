# Phase 1 Test Report: Ingestion, Cleaning, and PII Scrubbing

**Date:** 2026-11-11  
**Status:** PASS (55 passed, 0 failed, 0 skipped in Phase 1 suite; 70 total passed across suite)  
**Suite:** `tests/test_phase1.py`  

---

## Summary

All required Phase 1 test groups defined in `docs/edge-case.md` §16 (`ING-*`, `WIN-*`, `NRM-*`, `LNG-*`, `DUP-*`, `LOW-*`, `PII-01..20`, `PIIN-01..08`, `PII-30`, `PII-38`, `SEC-01`) have been executed and verified.

| Group | Test IDs Covered | Priority | Result | Key Capabilities Verified |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | `ING-01..10`, `ING-16` | P0 / P1 | **PASSED** | Explicit allowlist drops reviewer identity fields; BOM/CRLF/encodings handled; missing fields fail fast; re-ingestion is idempotent |
| **Time Window** | `WIN-01..04`, `WIN-06`, `WIN-08` | P1 | **PASSED** | 8-12 week bounds enforced; coverage shortfall flagged; ISO Monday start normalization; inclusive boundary matching |
| **Normalization** | `NRM-01..02` | P0 / P1 | **PASSED** | Zero-width / invisible characters stripped; emoji-only marked low-info |
| **Language** | `LNG-01..04` | P1 / P2 | **PASSED** | Devanagari Hindi and Roman Hinglish detected and marked quote-ineligible; uncertain falls back to `unknown` |
| **Deduplication** | `DUP-01..04` | P0 / P1 | **PASSED** | Exact SHA256 dedupe; near-duplicate shingle collapse; short generic reviews preserved across instances |
| **Low-Info Filter** | `LOW-01` | P0 | **PASSED** | Datasets dominated by emoji-only/empty text trigger pipeline halt |
| **PII Redaction** | `PII-01..20`, `PII-30`, `PII-38` | P0 | **PASSED** | Emails, phones (Indian/intl/split), PAN, Aadhaar, UPI IDs, account/txn IDs, URLs, handles, sign-offs, UUIDs, DOB redacted; quote_eligible=0 enforced |
| **Over-Redaction Guards** | `PIIN-01..08` | P1 / P2 | **PASSED** | Durations ("10 days"), currencies ("₹5000"), versions ("v14.3.0"), small counts, percentages, and brand words survive intact |
| **Security & Privacy** | `SEC-01` | P0 | **PASSED** | SQLite schema contains zero reviewer identity columns |

---

## Deliverables Verified

1. **Database Schema & Adapter:** `src/store/db.py` and `src/store/models.py` with tables for `reviews`, `runs`, `themes`, `review_themes`, and `publish_state`.
2. **Ingestion & Allowlist:** `src/ingest/play_csv.py` enforcing field allowlist (`rating`, `title`, `text`, `date`, `app_version`).
3. **Scrubber & Cleaning:** `src/clean/pii.py`, `src/clean/normalize.py`, `src/clean/lang.py`, `src/clean/dedupe.py`, and `src/clean/window.py`.
4. **CLI Command:** `python -m src.pipeline ingest --week <YYYY-MM-DD>` executes ingestion and outputs summary statistics.
5. **Raw Archive:** `data/raw/` contains allowlisted, PII-free copies of ingested batches.
