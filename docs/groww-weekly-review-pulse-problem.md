# Problem Statement: Groww Weekly Review Pulse

> Turn raw app-store feedback for **Groww (Stocks, Mutual Fund, IPO)** into a one-page weekly pulse that a team can scan in minutes: what users care about, what they actually said, and what to do next.

---

## 1. Overview

Groww receives a constant stream of public reviews on the Google Play Store and Apple App Store. These reviews are rich with signal (bugs, friction in KYC, payment failures, withdrawal delays, UI praise or complaints) but are too voluminous and unstructured for Product, Support, and Leadership to read directly.

This project builds an automated pipeline that:

1. Ingests recent public reviews (last 8-12 weeks).
2. Clusters them into a small set of themes (max 5).
3. Distills a **one-page weekly note** (≤250 words) with top themes, verbatim user quotes, and action ideas.
4. Publishes the note to **Google Docs**.
5. Creates a **Gmail draft** containing the note (or a clear pointer to it) addressed to yourself or an alias.

Google Docs and Gmail are accessed through **MCP (Model Context Protocol) servers**, not through hand-written Google API / OAuth / REST code.

**Primary source (Play Store):** https://play.google.com/store/apps/details?id=com.nextbillion.groww&hl=en_IN

---

## 2. Goals and Non-Goals

### Goals
- Give stakeholders a fast, trustworthy, scannable weekly health check of user sentiment.
- Ground every claim in real reviews: quotes are verbatim, themes are traceable to review counts.
- Produce concrete, theme-linked action ideas that Product/Growth and Support can act on.
- Keep the integration MCP-first so auth and HTTP plumbing are not reinvented.
- Guarantee that no PII appears in any generated artifact.

### Non-Goals
- Real-time review monitoring or alerting.
- Replying to reviews on the stores.
- Building a full analytics dashboard or historical BI system.
- Scraping behind store logins or any ToS-violating automation.
- Handling Google credentials or writing a bespoke OAuth/REST client as the primary integration path.

---

## 3. Audience and Value

| Audience | What they get |
|---|---|
| **Product / Growth** | Prioritized fixes and improvements backed by real user signals |
| **Support** | Messaging aligned with what users are actually saying; early view of recurring complaints |
| **Leadership** | One-page health check without drowning in raw reviews |

---

## 4. End-to-End Flow ("What Done Looks Like")

```
[Public review export]  -->  [Ingest + clean + anonymize]  -->  [Theme clustering (<=5)]
        |                                                              |
        |                                                              v
        |                                              [Weekly note generation (<=250 words)]
        |                                                              |
        |                                       +----------------------+----------------------+
        |                                       v                                             v
        |                            [Google Docs via MCP]                         [Gmail draft via MCP]
        |                            (pulse document)                              (note or link to doc)
```

**Definition of done:** a reviewer can run the pipeline for a given week and end up with (a) a one-page pulse in Google Docs and (b) a Gmail draft in their drafts folder that contains the note or links to it, with no PII anywhere.

---

## 5. Functional Requirements

### 5.1 Review Ingestion
- Import reviews from roughly the **last 8-12 weeks**.
- Sources: Google Play Store (Groww) and Apple App Store (Groww). Use whatever public export mechanism is available for each.
- Capture the fields the export provides, typically:
  - `rating` (1-5)
  - `title` (App Store usually has one; Play Store often does not)
  - `text` (review body)
  - `date`
  - Optional: `app_version`, `platform`, `language` (only if non-identifying)
- Support a configurable window (default 12 weeks, minimum 8).
- Deduplicate reviews (same text + date + platform).
- Store a normalized local dataset (CSV/JSON/SQLite) as the pipeline's single source of truth.

### 5.2 Cleaning and Privacy Scrubbing
- **Drop** reviewer names/usernames, profile identifiers, emails, device IDs, and any other reviewer metadata at ingestion; never carry them forward.
- Scan review text for embedded PII (phone numbers, emails, PAN/Aadhaar-like numbers, account/folio numbers, order or transaction IDs, names signed at the end of a review) and redact or exclude those reviews/snippets from quotes.
- Normalize whitespace and encoding; detect language and handle (or explicitly filter) non-English / Hinglish reviews.
- Filter obvious spam, empty, or one-word reviews from theme clustering (but keep them in the raw count if useful).

### 5.3 Theme Clustering
- Group reviews into **at most 5 themes**.
- Themes should fit the Groww product. Candidate examples (pick/merge what the data supports):
  - Onboarding / KYC / account opening
  - Payments / UPI / add-funds failures
  - Withdrawals / redemptions / settlement delays
  - App performance, crashes, login issues, glitches
  - Statements / reports / tax documents / portfolio views
  - Charges, brokerage, and pricing transparency
  - Customer support responsiveness
  - Positive UX / ease of investing / mutual fund and IPO experience
- Each theme must have: a short label, a one-line description, a review count, share of total, and average rating.
- Each review is assigned to a primary theme (or marked "Other/unclassified").
- Clustering approach is open (LLM-based labeling, embeddings + clustering, or keyword/rule hybrid) but must be reproducible and explainable.

### 5.4 Weekly One-Page Note
The note is **≤250 words** and must include:

1. **Top 3 themes**: a subset of the (≤5) themes, ranked by volume and/or severity, each with a one-line summary and a signal strength (count or share, sentiment).
2. **3 real user quotes**: verbatim snippets, anonymous, with no invented or paraphrased wording. Light trimming with an ellipsis is acceptable only if the meaning is unchanged and the words shown are exact.
3. **3 action ideas**: concrete, specific next steps, each tied to a theme (e.g., owner function, what to change or investigate, what success looks like).

Also include a header with the review window (e.g., "Reviews from DD Mon to DD Mon") and total reviews analyzed.

### 5.5 Google Docs Delivery (via MCP)
- Create (or update) a Google Doc titled with the week, e.g., `Groww Weekly Review Pulse: Week of YYYY-MM-DD`.
- The doc contains the one-page note, formatted for scanning (short headings, brief bullets, quotes visually distinct).
- Re-running for the same week should **update** rather than duplicate the document (or clearly version it).
- Return the document URL for use in the email.

### 5.6 Gmail Draft (via MCP)
- Create a **draft** (not send) addressed to yourself or an alias.
- Subject example: `Groww Weekly Review Pulse | Week of YYYY-MM-DD`.
- Body contains the full note **or** a short summary plus the Google Doc link (a clear pointer).
- No PII in subject, body, or attachments.

---

## 6. Integration Requirements: MCP First

- Use **MCP servers/connectors** for Google Docs and Gmail. Examples of what to call: "create document", "update document content", "create draft".
- Do **not** build a bespoke OAuth client plus REST wrapper for Google APIs as the primary path.
- The agent/app discovers and calls MCP tools; authentication is handled by the MCP server/connector configuration.
- Choose whichever Docs and Gmail MCP servers your environment provides; the requirement is **MCP-first**, not a specific vendor.
- Document in the README: which MCP servers were used, how they are configured (without secrets), and which tools are called.
- Handle MCP failures gracefully: retry with backoff, surface a clear error, and fall back to saving the note locally (Markdown) if Docs/Gmail is unavailable.

---

## 7. Constraints

| Constraint | Requirement |
|---|---|
| **Data source** | Public review exports only. No scraping behind store logins, no ToS-violating automation. |
| **Time window** | Roughly the last 8-12 weeks of reviews |
| **Themes** | Maximum **5** themes for clustering; the note highlights the top **3** |
| **Length** | Weekly note ≤ **250 words**, scannable |
| **Quotes** | Verbatim from real reviews, exactly 3 in the note, never fabricated |
| **Actions** | Exactly 3 concrete, theme-grounded action ideas |
| **Privacy** | No PII: no usernames, emails, device IDs, or other identifiable reviewer data in **any** artifact (datasets shared, Docs, emails, logs, screenshots) |
| **Credentials** | The pipeline does not handle Google credentials directly; auth lives in the MCP layer |

> **Compliance note:** Confirm the chosen collection method for each store complies with that store's terms. Prefer official/public export mechanisms (for example, Apple's public customer-reviews feed for the App Store, and a permitted public export for Google Play). Document the method and its limits in the README. Where a compliant automated export is unavailable, a manually exported public dataset is acceptable.

---

## 8. Data Model (Suggested)

**Raw / normalized review record**

| Field | Type | Notes |
|---|---|---|
| `review_id` | string | Internal hash, not the store's reviewer ID |
| `platform` | enum | `play_store` / `app_store` |
| `rating` | int (1-5) | |
| `title` | string \| null | |
| `text` | string | PII-scrubbed |
| `date` | date | |
| `app_version` | string \| null | Optional |
| `theme_id` | string \| null | Assigned after clustering |
| `sentiment` | enum \| null | Optional: positive / neutral / negative |

**Theme record**

| Field | Type |
|---|---|
| `theme_id` | string |
| `label` | string |
| `description` | string |
| `review_count` | int |
| `share_pct` | float |
| `avg_rating` | float |
| `candidate_quotes` | list of review_ids |

---

## 9. Weekly Note Template

Target: **≤250 words total.**

```markdown
# Groww Weekly Review Pulse | Week of <YYYY-MM-DD>
Window: <start> to <end> | Reviews analyzed: <N> | Avg rating: <x.x>

## Top 3 Themes
1. **<Theme A>** (<xx% of reviews>, avg <x.x>★): <one-line summary>
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

- **Traceable:** every theme count and quote can be traced back to the dataset.
- **Verbatim quotes:** copied exactly from source text; no rewording, no merging of multiple reviews into one quote.
- **Diverse quotes:** ideally cover different top themes rather than three quotes about the same issue.
- **Actionable:** each action names a concrete change or investigation, a likely owner (Product, Engineering, Support, Growth), and a measurable signal.
- **Balanced:** include a positive theme when it genuinely ranks in the top 3; don't only report complaints.
- **No overreach:** don't claim causes the reviews don't support; phrase as "users report..." not "the app is broken because...".
- **Concise:** if the draft exceeds 250 words, trim rather than shrink fonts or hide content.

---

## 11. Acceptance Criteria

- [ ] Reviews from roughly the last 8-12 weeks are imported from public exports for the Groww app.
- [ ] Reviews are clustered into **≤ 5** themes with label, count, share, and avg rating.
- [ ] The weekly note contains **top 3 themes**, **3 verbatim quotes**, and **3 action ideas**.
- [ ] The note is **≤ 250 words** and scannable.
- [ ] The note is created (or updated) as a **Google Doc via MCP**.
- [ ] A **Gmail draft via MCP** exists addressed to self/alias, containing the note or a clear link to it.
- [ ] A spot-check confirms every quote appears verbatim in the source dataset.
- [ ] A PII check on the dataset, Doc, and draft finds no usernames, emails, phone numbers, device IDs, or other identifiable data.
- [ ] No direct Google OAuth/REST client code is used as the primary integration path.
- [ ] Re-running for the same window does not create duplicate docs/drafts uncontrollably (idempotent or clearly versioned).
- [ ] README documents setup, data source method, MCP servers used, and how to run the pipeline.

---

## 12. Edge Cases to Handle

- Fewer reviews than expected in the window (low-volume week): still produce the note and flag low sample size.
- Highly skewed week (e.g., an outage causing a spike in one theme): note the spike and its share.
- Reviews in Hindi, Hinglish, or mixed scripts: translate for theme assignment if needed, but quote only in the original verbatim text, or skip non-English quotes.
- Reviews containing PII in the body: exclude from quote candidates and redact in stored text.
- Very short or generic reviews ("good", "nice app") dominating counts: handle so they don't crowd out actionable themes.
- Duplicate or bot-like reviews: deduplicate/filter.
- MCP tool failures or auth expiry: clear error and local Markdown fallback.
- Ratings and text mismatch (5 stars with a complaint): rely on text for theme assignment, report rating separately.

---

## 13. Suggested Architecture and Project Layout

```
groww-review-pulse/
├── README.md
├── data/
│   ├── raw/                  # public review exports (PII-stripped on ingest)
│   └── processed/            # normalized reviews + theme assignments
├── src/
│   ├── ingest/               # play store + app store importers
│   ├── clean/                # normalization, dedupe, PII scrubbing
│   ├── themes/               # clustering + labeling
│   ├── note/                 # note generation (word-count enforced)
│   ├── mcp/                  # MCP client wrappers: docs + gmail tool calls
│   └── pipeline.py|ts        # orchestrates the full weekly run
├── prompts/                  # LLM prompts for theming + note writing
├── tests/                    # PII, quote-verbatim, word-count, theme-cap tests
└── outputs/                  # local copy of weekly notes (Markdown)
```

**Pipeline stages:** `ingest → clean/anonymize → cluster (≤5) → select top 3 + quotes → generate note (≤250 words) → validate → publish to Docs (MCP) → create Gmail draft (MCP)`.

**Validation gate before publishing:**
1. Word count ≤ 250
2. Exactly 3 themes, 3 quotes, 3 actions
3. Every quote found verbatim in the dataset
4. PII scan passes on the final note

If any check fails, regenerate or fail loudly; do not publish.

---

## 14. Deliverables

1. **Working pipeline** (code/agent workflow) that runs the end-to-end flow.
2. **Normalized review dataset** (PII-free) covering the 8-12 week window.
3. **Theme summary** (≤5 themes with counts, shares, avg ratings).
4. **Weekly one-page pulse** (≤250 words) as a Google Doc.
5. **Gmail draft** containing the note or a pointer to the Doc.
6. **README** covering data-source method, MCP servers/tools used, how to run, and the privacy approach.
7. *(Optional)* Sample output Markdown and a short demo recording or screenshots (PII-free).

---

## 15. Evaluation Rubric (Suggested)

| Area | What good looks like |
|---|---|
| **Data ingestion** | Correct window, public/compliant source, clean normalized fields |
| **Theming** | ≤5 coherent, non-overlapping, product-relevant themes with metrics |
| **Note quality** | ≤250 words, scannable, top 3 themes, 3 verbatim quotes, 3 specific actions |
| **MCP integration** | Docs and Gmail handled through MCP tools; no custom OAuth/REST as primary path |
| **Privacy** | Zero PII across all artifacts; automated check present |
| **Reliability** | Idempotent reruns, error handling, validation gate |
| **Communication** | Clear README and rationale for design choices |

---

## 16. Open Questions / Decisions to Make

- Which compliant public export method will be used for Google Play reviews, and what are its rate/volume limits?
- Which App Store region(s) to include (e.g., India only) and how to handle multiple languages?
- Clustering approach: LLM labeling, embeddings plus clustering, or a hybrid?
- Ranking rule for "top 3": by volume, by negative-sentiment weight, or a combined severity score?
- Which Docs and Gmail MCP servers will be used, and how is auth configured on the MCP side?
- Draft recipient: personal address or a team alias?
- Run cadence: manual trigger or scheduled weekly job?

---

## 17. Glossary

- **MCP (Model Context Protocol):** a standard for exposing tools (e.g., Docs, Gmail actions) to an agent or app so it can call them without bespoke API integration.
- **Pulse:** the short weekly summary of user feedback.
- **PII:** personally identifiable information, such as names, usernames, emails, phone numbers, device IDs, or financial identifiers.
- **Theme:** a cluster of reviews sharing a common topic (e.g., KYC, payments, withdrawals).
