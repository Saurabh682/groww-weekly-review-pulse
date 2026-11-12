# Phase 2 Test Report: Theme Engine & User Constraints

**Date:** 2026-11-11  
**Status:** PASS (21 passed, 0 failed, 0 skipped in Phase 2 suite; 91 total passed across complete regression suite)  
**Suite:** `tests/test_phase2.py`  

---

## Summary

All required Phase 2 capabilities and test groups defined in `docs/edge-case.md` §16 (`THM-*`, `LBL-*`) along with the **user-specified filtering constraints** have been implemented, tested, and verified.

| Group | Test IDs Covered | Priority | Result | Key Capabilities Verified |
| :--- | :--- | :--- | :--- | :--- |
| **User Constraints** | `USER-01` | P0 | **PASSED** | Only reviews with strictly **> 8 words** (`len(text.split()) > 8`) are retained for theme analysis |
| **User Constraints** | `USER-02` | P0 | **PASSED** | All emojis are stripped cleanly from review text without corrupting Latin, numeric, or punctuation characters |
| **User Constraints** | `USER-03` | P0 | **PASSED** | English-only filtering enforced; Hindi (`hi`), Hinglish, and non-English reviews are filtered out |
| **Clustering Engine** | `THM-01..03`, `THM-05..08` | P0 / P1 | **PASSED** | Hard cap of $k \le 5$ clusters; determinism under fixed seed; tiny cluster merge ($< 5\%$ to nearest centroid); small sample fallback |
| **Embedding & Cache** | `THM-10..11` | P0 / P1 | **PASSED** | Deterministic TF-IDF + LSA embedding; SQLite caching in `embedding_cache` keyed by `(review_id, model_name)`; clean error on empty input |
| **Ranking & Scoring** | `THM-12..18` | P1 / P2 | **PASSED** | Priority scoring `0.4 * share + 0.6 * neg_share`; uniform rating safe; deterministic tie-breaking; positive dominance guard (top 3 must contain $\ge 1$ critical theme when negative share $\ge 10\%$); outage spike detection ($\Delta \ge 15\%$ or $2\times$) |
| **Labeling Safety** | `THM-19..20`, `LBL-02..03` | P0 / P1 | **PASSED** | Concise labels ($\le 4$ words); brief descriptions ($\le 15$ words); zero PII tokens; distinct per cluster; prior week label affinity |

---

## Real Play Store Data Validation

The theme engine was executed against **3,600 real public Play Store reviews** for Groww (`com.nextbillion.groww`):

- **Pre-filtering input:** 1,435 window-qualified, non-low-info reviews
- **After user filtering rules:** **662 reviews** kept
  - 713 reviews discarded (words $\le 8$)
  - 60 reviews discarded (non-English / Hindi)
  - 128 reviews had emojis stripped
- **Themes Generated & Ranked:**
  1. **Charges & Pricing** (Share: 24.9%, Avg Rating: 1.83★, Neg Share: 77.0%, Top 3: Yes)
  2. **App Performance & Bugs** (Share: 22.2%, Avg Rating: 2.12★, Neg Share: 70.1%, Top 3: Yes)
  3. **Customer Support** (Share: 14.8%, Avg Rating: 1.88★, Neg Share: 74.5%, Top 3: Yes)
  4. **Platform Feedback** (Share: 17.5%, Avg Rating: 2.87★, Neg Share: 49.1%, Top 3: No)
  5. **Positive UX & Simplicity** (Share: 20.5%, Avg Rating: 4.63★, Neg Share: 5.1%, Top 3: No)

---

## Deliverables Verified

1. **User Filter Module:** `src/themes/filter.py` implementing `apply_user_phase2_filters()` with `> 8` words check, emoji stripping via `src/clean/normalize.py:remove_emojis()`, and language filter.
2. **Embedding & Cache Module:** `src/themes/embed.py` implementing `Embedder` with TF-IDF + LSA and SQLite `embedding_cache`.
3. **Clustering Engine:** `src/themes/cluster.py` with silhouette-based $k \in [2, 5]$ selection, deterministic seeds, and tiny cluster absorption.
4. **Labeler:** `src/themes/label.py` generating PII-checked labels ($\le 4$ words) and descriptions ($\le 15$ words) using domain keyword scoring and TF-IDF extraction.
5. **Ranking Engine:** `src/themes/rank.py` computing volume share, negative share, composite priority score, positive dominance policy, and spike detection.
6. **Pipeline Integration:** `src/pipeline.py themes` sub-command persisting runs and themes into SQLite `runs` and `themes` tables.
