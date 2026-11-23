---
title: Groww Weekly Review Pulse Backend
emoji: 📈
colorFrom: green
colorTo: indigo
sdk: static
short_description: Backend ML pipeline, clustering & MCP engine for Groww Pulse
---

# 📈 Groww Weekly Review Pulse — Backend & ML Pipeline Engine

Turn raw Google Play Store feedback for **Groww (Stocks, Mutual Fund, IPO)** into a one-page weekly executive note that product and leadership teams can scan in 90 seconds.

---

## 🔗 Live Deployments & Ecosystem

- **Frontend Web App (Vercel)**: [https://groww-weekly-review-pulse-frontend.vercel.app](https://groww-weekly-review-pulse-frontend.vercel.app)
- **Source Code (GitHub)**: [https://github.com/Saurabh682/groww-weekly-review-pulse](https://github.com/Saurabh682/groww-weekly-review-pulse)
- **Backend Hub (Hugging Face Spaces)**: [https://huggingface.co/spaces/deamonizer/groww-weekly-review-pulse-backend](https://huggingface.co/spaces/deamonizer/groww-weekly-review-pulse-backend)

---

## 🏗️ Architecture & Pipeline Phases

The backend pipeline executes 5 deterministic phases:

1. **Phase 1: Ingestion & Schema Normalization**:
   - Ingests public Google Play reviews via allowlisted schema (`review_id`, `text`, `rating`, `timestamp`, `app_version`).
   - Normalizes UTC ISO timestamps and cleans extraneous metadata.
2. **Phase 2: Hygiene, Language & Zero-PII Guard**:
   - Deduplication: SHA-256 fingerprinting on normalized text.
   - Low-Info Filter: Discards reviews with $\le 8$ words or trivial tokens ("good", "bad", "ok").
   - Multi-Lingual Filter: English reviews retained; foreign language reviews filtered out.
   - PII Scrubbing: Multi-pass regex engine with negative lookahead protecting time, versions, and currency while strictly redacting phone numbers, emails, PAN, Aadhaar, and order IDs.
3. **Phase 3: TF-IDF & K-Means Clustering**:
   - Semantic TF-IDF vectorization with unigram + bigram representations.
   - K-Means clustering with optimal cluster heuristic clamped strictly to $\le 5$ clusters.
   - Priority Scoring: $Priority = (Share\% \times 0.4) + (NegShare\% \times 0.4) + ((5 - Rating) \times 10 \times 0.2)$.
4. **Phase 4: Note Generation & 6-Gate Invariant Validation**:
   - Synthesizes 90-second executive memo.
   - Hard Quality Gates: Word count $\le 250$, exactly 3 top themes, 3 verbatim quotes, 3 actionable items, $\le 5$ clusters, 0 PII.
   - Failsafe: Any gate violation blocks publication immediately (`INV-02`).
5. **Phase 5: MCP Publishing**:
   - Creates/updates Google Doc via Google Docs MCP.
   - Stages Gmail draft via Gmail MCP (strictly "Draft only", never automated send).

---

## 📊 Invariant Matrix

| Code | Invariant Name | Strict Enforcement Rule |
| :--- | :--- | :--- |
| **INV-01** | Word Count Limit | Total plain word count $\le 250$ (markdown formatting stripped) |
| **INV-02** | Validation Gate | Invariant failures unconditionally abort delivery |
| **INV-03** | Theme Parity | Exactly 3 top themes included in executive note |
| **INV-04** | Verbatim Authenticity | Exactly 3 quotes matching ingested Google Play review IDs |
| **INV-05** | Ownership Action | Exactly 3 action ideas with owners (`Engineering`, `Product`, `Growth/Support`) |
| **INV-06** | Cluster Ceiling | Number of theme clusters is bounded at $\le 5$ |
| **INV-07** | Zero-PII Guarantee | 0 sensitive customer tokens anywhere in published artifacts |

---

## 💻 CLI Usage

```bash
# Run tests
pytest tests/ -v

# Run the pipeline for a specific week
python -m src.pipeline --week 2026-11-09 --dry-run

# Run with full MCP publishing
python -m src.pipeline --week 2026-11-09
```
