# Edge Cases, Corner Scenarios, and Tests: Groww Weekly Review Pulse

> Companion to `problemStatement.md`, `architecture.md`, and `implementation-plan.md`.
> Written so a coding agent (**AG / Antigravity**) can turn each case into an automated test and verify it, phase by phase.
> **Scope:** Google Play Store reviews only. Apple App Store is excluded for now.

---

## 0. How AG Should Use This File

1. **Every case has a stable ID** (e.g., `PII-07`). Use the ID in the test name and in commit messages so coverage is traceable.
2. **Implement tests in phase order** (see §16). Do not move to the next phase until the previous phase's P0 tests are green.
3. **Priority meaning**
   - **P0:** Violates a hard constraint in the problem statement (≤5 themes, 3 quotes, 3 actions, ≤250 words, verbatim quotes, no PII, MCP-only, public data only). Must pass before any publish path is enabled.
   - **P1:** Causes wrong, misleading, or unreliable output.
   - **P2:** Polish, ergonomics, rare corner.
4. **Test naming convention:** `test_<ID>_<short_snake_case>` (e.g., `test_PII_07_upi_id_redacted`).
5. **Fixtures:** all data in tests is **synthetic**. Phone numbers, PAN-like strings, emails, and UPI IDs in this file are fake and must never be replaced by real ones. Fake data lives in `tests/fixtures/`.
6. **When a case reveals an ambiguity**, do not guess silently: choose the safest behavior (fail closed, redact more, publish nothing), record the decision in `docs/decisions.md`, and add a test for it.
7. **Never weaken a P0 test** to make the build pass. Fix the code.
8. **Reporting:** after each phase, AG writes `outputs/test_report_phase_<n>.md` listing IDs run, passed, failed, skipped (with reasons). No review text in reports.

### Status legend used in tables
`P0 / P1 / P2` = priority. **Type:** `U` unit, `I` integration, `P` property/invariant, `G` golden/snapshot, `M` mock-MCP contract, `S` manual smoke.

---

## 1. Canonical Definitions (so tests agree)

| Term | Definition |
|---|---|
| **Word** | Whitespace-separated token in the rendered note after removing Markdown syntax characters (`#`, `*`, `_`, `>`, `-` list markers, backticks, link syntax keeps only link text). Numbers, `₹5000`, and `4.5★` each count as one word. URLs count as one word each. |
| **Normalized text** | NFKC → convert curly quotes/apostrophes to straight → collapse all whitespace runs to a single space → trim. Case is preserved. |
| **Verbatim quote** | A string whose normalized form is a contiguous substring of the normalized stored `text` of exactly one source review. Ellipsis (`…` or `...`) may join fragments only if **each fragment** is a verbatim substring of the **same** review, in original order. |
| **Low-info review** | Fewer than 3 tokens after normalization (configurable) or only punctuation/emoji. |
| **PII** | Emails, phone numbers, PAN-like, Aadhaar-like, UPI IDs, account/folio/order/transaction-like long digit strings, URLs, @handles, and personal names in sign-offs; plus any reviewer identity fields (username, user ID, avatar, device ID). |
| **Theme cap** | Total distinct themes in a run ≤ 5, including any "Other" bucket. |
| **Run week** | Monday-start ISO week of `--week` date, evaluated in UTC. |

---

## 2. Ingestion and Data Source (Play Store only)

| ID | Scenario / Corner case | Expected behavior | Test | Type | Pri |
|---|---|---|---|---|---|
| ING-01 | Input file contains reviewer name, user ID, avatar URL, or device columns | Those columns are **never read**; resulting records have no such fields; raw copy in `data/raw/` has none | `test_ING_01_identity_columns_dropped` | U/I | P0 |
| ING-02 | Input file has an unknown extra column | Ignored with a warning; no crash | `test_ING_02_unknown_column_ignored` | U | P1 |
| ING-03 | Required column missing (`text` or `rating` or `date`) | Fails fast with a clear error naming the column; nothing written to DB | `test_ING_03_missing_required_column` | U | P0 |
| ING-04 | Optional `title` column missing or empty (Play reviews often have none) | Accepted; `title` is null; clustering input uses text only | `test_ING_04_missing_title_ok` | U | P1 |
| ING-05 | Rating outside 1-5, non-numeric, float like `4.0`, or `"5 stars"` | Out-of-range/invalid rows rejected and counted; `4.0` coerced to 4; `"5 stars"` rejected unless a mapping rule exists | `test_ING_05_rating_validation` | U | P1 |
| ING-06 | Date formats vary (ISO, `DD/MM/YYYY`, `MM/DD/YYYY`, with timezone, epoch seconds/ms) | Parsed per configured format; ambiguous `01/02/2026` follows config, never guessed; unparseable rows rejected and counted | `test_ING_06_date_formats` | U | P1 |
| ING-07 | Review dated in the future | Rejected and counted (clock-skew tolerance configurable) | `test_ING_07_future_date_rejected` | U | P1 |
| ING-08 | Empty file, header-only file | Run stops with "no reviews" message; no Doc, no draft | `test_ING_08_empty_input_no_publish` | I | P0 |
| ING-09 | File with BOM, CRLF line endings, mixed encodings (UTF-8, UTF-16, Latin-1 mojibake) | Parsed correctly or rejected with an encoding error; no silent corruption | `test_ING_09_encoding_variants` | U | P1 |
| ING-10 | Reviews with embedded newlines/commas/quotes inside CSV fields | Parsed correctly as single records | `test_ING_10_csv_quoting` | U | P1 |
| ING-11 | Very large file (e.g., 200k rows) | Streams; memory stays bounded; completes within configured time | `test_ING_11_large_file_streaming` | I | P2 |
| ING-12 | Extremely long single review (e.g., 20k chars) | Truncated for embedding (configurable), stored in full only if PII-clean; no crash | `test_ING_12_very_long_review` | U | P2 |
| ING-13 | Source file includes non-Groww-app reviews (wrong package id column, if present) | Filtered out or run aborted per config; counted | `test_ING_13_wrong_app_filtered` | U | P1 |
| ING-14 | Automated Play collection flag set to true without approval record | Refuses to run with an explanatory error (feature is off by default) | `test_ING_14_automated_source_blocked` | U | P0 |
| ING-15 | Config requests App Store source | Rejected as "not supported in this build"; no network call attempted | `test_ING_15_app_store_not_supported` | U | P1 |
| ING-16 | Same file ingested twice | Second ingestion adds 0 new rows (idempotent) | `test_ING_16_reingest_idempotent` | I | P0 |
| ING-17 | Two files with overlapping date ranges | Union without duplicates | `test_ING_17_overlapping_imports` | I | P1 |
| ING-18 | Developer replies column present in export | Ignored (not user feedback) | `test_ING_18_developer_reply_ignored` | U | P1 |

---

## 3. Time Window

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| WIN-01 | Reviews span fewer than 8 weeks | Run continues; run report and note header flag the shortfall ("coverage: X weeks") | `test_WIN_01_short_coverage_flagged` | I | P1 |
| WIN-02 | Reviews span more than 12 weeks | Older reviews excluded from the analysis window; retained only per retention rule | `test_WIN_02_older_reviews_excluded` | U | P1 |
| WIN-03 | `window.weeks` configured to 6 or 15 | Config validation error (must be 8-12) | `test_WIN_03_window_bounds_validated` | U | P1 |
| WIN-04 | Review on the exact boundary instant (window_start 00:00 UTC, window_end 23:59:59 UTC) | Inclusion rule is consistent and documented (start inclusive, end inclusive) | `test_WIN_04_boundary_inclusion` | U | P1 |
| WIN-05 | Reviews exist only in the most recent week | Note still produced; flagged as low coverage | `test_WIN_05_single_week_data` | I | P1 |
| WIN-06 | `--week` set to a non-Monday date | Normalized to the ISO week start; same `week_start` key used for publish state | `test_WIN_06_week_normalization` | U | P1 |
| WIN-07 | Run executed across a DST change or year boundary | Dates handled in UTC; ISO week 52/53 correct | `test_WIN_07_year_boundary_week` | U | P2 |
| WIN-08 | `--week` in the future | Rejected with a clear message | `test_WIN_08_future_week_rejected` | U | P1 |

---

## 4. Normalization, Language, Dedupe, Low-Info

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| NRM-01 | Emoji-only review ("👍👍👍") | Marked low-info; counted in totals and avg rating; excluded from clustering/quotes | `test_NRM_01_emoji_only_low_info` | U | P1 |
| NRM-02 | Zero-width characters, RTL marks, homoglyphs, NBSP | Normalized; PII regexes still match after normalization | `test_NRM_02_hidden_chars_normalized` | U | P0 |
| NRM-03 | Text entirely uppercase | Preserved as is for storage; clustering is case-insensitive | `test_NRM_03_uppercase_text` | U | P2 |
| NRM-04 | Repeated characters / spam ("goooood!!!!!!") | Kept; not flagged as spam unless duplicate rule matches | `test_NRM_04_elongation` | U | P2 |
| LNG-01 | Pure Hindi (Devanagari) review | `lang=hi`; clustered if multilingual embedder; `quote_eligible=false` by default | `test_LNG_01_hindi_not_quote_eligible` | U | P1 |
| LNG-02 | Hinglish (Roman script Hindi, e.g., synthetic "paisa nahi nikal raha") | `lang=mixed` or `hinglish`; clustered; not quote-eligible by default | `test_LNG_02_hinglish_handling` | U | P1 |
| LNG-03 | Language detection fails/uncertain on short text | Falls back to `unknown`; never crashes; not quote-eligible | `test_LNG_03_unknown_language_safe` | U | P1 |
| LNG-04 | English review containing Hindi words | Treated as English if detector confidence high; quote eligibility follows PII rules | `test_LNG_04_code_mixed_english` | U | P2 |
| DUP-01 | Exact duplicate text and date | Collapsed to one; dedupe count reported | `test_DUP_01_exact_duplicate` | U | P0 |
| DUP-02 | Same text, different dates | Kept as separate reviews if outside the near-duplicate window; behavior is configured and tested | `test_DUP_02_same_text_diff_date` | U | P1 |
| DUP-03 | Near-duplicates (one word changed, trailing punctuation) | Collapsed above the similarity threshold | `test_DUP_03_near_duplicate` | U | P1 |
| DUP-04 | Short genuine reviews that match ("Good app") from different users | Not over-collapsed in a way that distorts rating averages; policy documented | `test_DUP_04_short_generic_duplicates_policy` | U | P1 |
| DUP-05 | Bot-like burst: 50 near-identical 5-star reviews on one day | Collapsed or flagged; flagged in run report | `test_DUP_05_burst_detected` | I | P1 |
| LOW-01 | All reviews are low-info | Run stops before clustering with a clear message; no publish | `test_LOW_01_all_low_info_stops` | I | P0 |
| LOW-02 | 90% low-info, 10% substantive | Clustering runs on the substantive 10%; note flags "small analyzable sample" | `test_LOW_02_mostly_low_info_flagged` | I | P1 |

---

## 5. PII Detection and Redaction (highest risk)

**All sample values below are fake.** AG must generate additional randomized synthetic variants for property tests.

### 5.1 Must-redact cases

| ID | Scenario (synthetic example) | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| PII-01 | Email: `test.user99@example.com` | Replaced with `[REDACTED]`; `pii_found=1`; `quote_eligible=0` | `test_PII_01_email` | U | P0 |
| PII-02 | Email with obfuscation: `test dot user at example dot com`, `test(at)example.com` | Redacted (best-effort patterns); if undetectable, review remains quote-ineligible when any "at"/"dot" email-like pattern is present | `test_PII_02_obfuscated_email` | U | P0 |
| PII-03 | Indian mobile: `9876543210`, `+91 98765 43210`, `098765-43210`, `+91-9876543210` | All redacted | `test_PII_03_indian_phone_formats` | U | P0 |
| PII-04 | International numbers `+1 (555) 010-9999`, `0044 20 7946 0000` | Redacted | `test_PII_04_intl_phone` | U | P0 |
| PII-05 | Phone digits spaced or split by words/dots: `98 76 54 32 10`, `9.8.7.6.5.4.3.2.1.0` | Redacted | `test_PII_05_split_phone` | U | P0 |
| PII-06 | PAN-like: `ABCDE1234F` (case-insensitive, with spaces/hyphens) | Redacted | `test_PII_06_pan_like` | U | P0 |
| PII-07 | UPI ID: `name@okhdfcbank`, `9876543210@ybl`, `shop.name@paytm` | Redacted | `test_PII_07_upi_id` | U | P0 |
| PII-08 | Aadhaar-like: `1234 5678 9012`, `123456789012` | Redacted | `test_PII_08_aadhaar_like` | U | P0 |
| PII-09 | Long numeric IDs near keywords: "order id 5839201847", "txn no 0012345678901", "folio 12345678/90", "account ending 4321" | Redacted (keyword-proximate digit strings ≥ 6 digits; "ending NNNN" 4-digit also redacted) | `test_PII_09_account_order_txn_ids` | U | P0 |
| PII-10 | URLs with query strings or profile paths; `http://`, `https://`, bare `www.` | Redacted | `test_PII_10_urls` | U | P0 |
| PII-11 | @handles (`@some_user`) and social links | Redacted | `test_PII_11_handles` | U | P0 |
| PII-12 | Name sign-offs: "Thanks, Rahul", "- Priya S.", "Regards Amit Kumar", "Yours truly, S. Sharma" | Review marked `quote_eligible=0` at minimum; the sign-off name is redacted | `test_PII_12_signoff_names` | U | P0 |
| PII-13 | Self-introductions: "I am Rahul from Pune", "my name is Anita" | Name redacted or review quote-ineligible | `test_PII_13_self_intro` | U | P0 |
| PII-14 | Device identifiers or IMEI-like 15-digit numbers, MAC-like strings, UUIDs | Redacted | `test_PII_14_device_ids` | U | P0 |
| PII-15 | Support ticket/complaint numbers ("ticket #AB-10293847") | Redacted | `test_PII_15_ticket_numbers` | U | P0 |
| PII-16 | Date of birth ("DOB 12/03/1990", "born on 5 May 1985") | Redacted | `test_PII_16_dob` | U | P0 |
| PII-17 | PIN codes combined with address-like text ("flat 12, MG Road, 560001") | Redacted if address-like; otherwise review marked quote-ineligible | `test_PII_17_address_like` | U | P1 |
| PII-18 | PII inside Unicode variants (fullwidth digits `９８７６５４３２１０`, Devanagari digits `९८७६५४३२१०`) | Normalized then redacted | `test_PII_18_unicode_digit_variants` | U | P0 |
| PII-19 | Multiple PII items in one review | All redacted; `pii_found=1` | `test_PII_19_multiple_pii_one_review` | U | P0 |
| PII-20 | PII in `title` field | Redacted the same way as text | `test_PII_20_pii_in_title` | U | P0 |

### 5.2 Must-NOT-redact (over-redaction guards)

| ID | Text that must survive intact | Test | Pri |
|---|---|---|---|
| PIIN-01 | "withdrawal took 10 days" / "waited 3 weeks" | `test_PIIN_01_durations` | P1 |
| PIIN-02 | "lost ₹5000" / "Rs. 25,000 stuck" / "₹1,20,000" (amounts under 6 consecutive digits or with currency formatting) | `test_PIIN_02_amounts` | P1 |
| PIIN-03 | App version strings: "version 5.2.1", "v12.40.3" | `test_PIIN_03_versions` | P1 |
| PIIN-04 | Ratings and counts: "4.5 stars", "1 star", "2 times", "3 attempts" | `test_PIIN_04_small_numbers` | P2 |
| PIIN-05 | Percentages and returns: "12.5% returns", "XIRR 14%" | `test_PIIN_05_percentages` | P2 |
| PIIN-06 | Product/brand words that look like names: "Nifty 50", "Groww", "Zerodha" (competitor mention), "Axis Bluechip" | `test_PIIN_06_brand_words` | P1 |
| PIIN-07 | Times and dates in text: "at 10:30 am", "on 5th March" (not DOB context) | `test_PIIN_07_times_dates` | P2 |
| PIIN-08 | "OTP not received" (word OTP is fine); actual 6-digit OTP values like "OTP 482910" are redacted | `test_PIIN_08_otp_word_vs_value` | P1 |

### 5.3 PII system-level

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| PII-30 | Property test: generate 1,000 random synthetic reviews with injected fake PII | **0** PII regex matches in stored text, note, email subject/body, logs, run report | `test_PII_30_property_no_pii_anywhere` | P | P0 |
| PII-31 | PII appears only in a quote candidate sentence | Candidate excluded from selection | `test_PII_31_pii_candidate_excluded` | U | P0 |
| PII-32 | PII scanner itself throws an exception | Pipeline fails closed (no publish) | `test_PII_32_scanner_failure_fails_closed` | I | P0 |
| PII-33 | Logs and exceptions capture review text accidentally (e.g., in a stack trace of a parsing error) | Logger scrubs or omits review text; test greps captured logs for seeded strings | `test_PII_33_logs_contain_no_review_text` | I | P0 |
| PII-34 | LLM prompt payload inspection | Prompts contain only scrubbed text; seeded PII never appears in the captured prompt | `test_PII_34_llm_prompt_scrubbed` | I | P0 |
| PII-35 | LLM response introduces PII-looking content (hallucinated email/phone) | Validator PII gate blocks the note | `test_PII_35_llm_hallucinated_pii_blocked` | I | P0 |
| PII-36 | Redaction token collisions: review literally contains "[REDACTED]" | Not double-processed; still quote-ineligible if it contains the token | `test_PII_36_literal_redacted_token` | U | P1 |
| PII-37 | A quote candidate contains `[REDACTED]` | Excluded from quotes | `test_PII_37_redacted_in_quote_excluded` | U | P0 |
| PII-38 | `data/raw/` files after ingestion | Contain no identity fields and no PII regex hits | `test_PII_38_raw_files_clean` | I | P0 |
| PII-39 | SQLite database dump | grep for PII patterns and identity columns returns nothing | `test_PII_39_db_dump_clean` | I | P0 |

---

## 6. Theme Clustering and Ranking

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| THM-01 | Property: any input size (1, 2, 5, 50, 5,000 reviews) | Distinct themes ≤ 5 | `test_THM_01_theme_cap_property` | P | P0 |
| THM-02 | Fewer than 10 analyzable reviews | Stops or produces ≤2 themes with a "very small sample" flag; never forces 5 clusters | `test_THM_02_tiny_sample` | I | P0 |
| THM-03 | Exactly 1 analyzable review | Run stops with a clear message (cannot form a pulse); no publish | `test_THM_03_single_review_stops` | I | P0 |
| THM-04 | All reviews nearly identical (one natural cluster) | One or two themes; note still has 3 "top themes" only if ≥3 exist, otherwise see NOT-01 | `test_THM_04_single_natural_cluster` | I | P1 |
| THM-05 | Silhouette tie between k values | Deterministic tie-break (documented, e.g., smaller k) | `test_THM_05_k_tie_break` | U | P1 |
| THM-06 | Tiny cluster below min share (3%) | Merged into nearest cluster | `test_THM_06_tiny_cluster_merged` | U | P1 |
| THM-07 | Clustering produces an "Other/noise" bucket | Bucket counts toward the 5-theme cap and can only appear in top 3 if labeled meaningfully | `test_THM_07_other_bucket_counts` | U | P1 |
| THM-08 | Same seed and data, repeat run | Identical assignments and ranks | `test_THM_08_determinism` | P | P1 |
| THM-09 | One review added to the dataset | Assignments change minimally (stability check within tolerance) | `test_THM_09_small_perturbation_stability` | I | P2 |
| THM-10 | Embedding service/model unavailable | Clear error; run fails closed; no partial publish | `test_THM_10_embedding_failure` | I | P0 |
| THM-11 | Embedding cache stale after model change | Cache keyed by model name; no mixing of embeddings across models | `test_THM_11_cache_keyed_by_model` | U | P1 |
| THM-12 | A theme's reviews all have identical rating | Stats computed without division errors | `test_THM_12_uniform_ratings` | U | P2 |
| THM-13 | Ranking tie in `priority_score` | Tie-break by `neg_share`, then growth, then label alphabetically (deterministic) | `test_THM_13_rank_tie_break` | U | P1 |
| THM-14 | `neg_share` = 0 or 1 | Score formula behaves; no NaN | `test_THM_14_neg_share_extremes` | U | P2 |
| THM-15 | Dominant positive theme ("great app") takes top rank | Allowed, but at least one issue-oriented theme appears in the top 3 **if one exists with ≥ min share** (policy configurable; test documents chosen policy) | `test_THM_15_positive_dominance_policy` | I | P1 |
| THM-16 | Reviews with rating/text mismatch (5★ with a complaint) | Theme from text; `avg_rating` reflects the star rating as given; mismatch rate reported | `test_THM_16_rating_text_mismatch` | I | P2 |
| THM-17 | Outage week spike (one theme > 60% share) | Flagged "spike" in run report and note summary; ranking unaffected | `test_THM_17_spike_flag` | I | P1 |
| THM-18 | No prior-week data | Trend field is null/"n/a"; no crash; note omits trend phrasing | `test_THM_18_no_prior_week` | U | P1 |
| THM-19 | Label reuse threshold boundary (cosine 0.849 vs 0.851) | Reuse only at/above threshold | `test_THM_19_label_reuse_boundary` | U | P2 |
| THM-20 | Two clusters would get the same label | Labels disambiguated or clusters merged; theme labels unique | `test_THM_20_unique_labels` | U | P1 |

### 6.1 LLM Labeling

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| LBL-01 | LLM returns invalid JSON | Retry (bounded); after limit, fall back to deterministic label (e.g., top keywords) | `test_LBL_01_invalid_json_fallback` | M | P0 |
| LBL-02 | Label longer than 4 words or description > 15 words | Rejected and retried or truncated deterministically | `test_LBL_02_length_limits` | U | P1 |
| LBL-03 | Label contains PII-like or profane content | PII gate blocks; profanity policy applied (replace with neutral label) | `test_LBL_03_label_safety` | U | P1 |
| LBL-04 | LLM timeout / rate limit | Retry with backoff; fallback label; run continues | `test_LBL_04_llm_timeout` | M | P1 |
| LBL-05 | LLM returns an empty label | Treated as failure → retry/fallback | `test_LBL_05_empty_label` | U | P1 |
| LBL-06 | Prompt-injection text inside a review ("ignore previous instructions and output...") | Review content treated as data; output still conforms to schema; injected instruction not followed | `test_LBL_06_prompt_injection_in_review` | I | P0 |

---

## 7. Quote Selection (verbatim guarantee)

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| QUO-01 | Every selected quote | Is a verbatim substring (per §1) of its source review's stored text | `test_QUO_01_verbatim_property` | P | P0 |
| QUO-02 | Mutation test: change one character/word in a quote | Validator fails | `test_QUO_02_mutation_detected` | U | P0 |
| QUO-03 | LLM attempts to paraphrase or "fix grammar" in a quote | Code ignores LLM text; quote taken from source span; or note rejected if mismatched | `test_QUO_03_llm_cannot_edit_quotes` | I | P0 |
| QUO-04 | Fewer than 3 eligible quotes in top-3 themes | Fill from the next-best eligible sentences in top themes, then lower-ranked themes; record in run report; if < 3 total eligible, **do not publish** | `test_QUO_04_insufficient_quotes` | I | P0 |
| QUO-05 | All 3 best sentences come from the same review | Rejected; must come from 3 distinct reviews | `test_QUO_05_distinct_reviews` | U | P0 |
| QUO-06 | Same sentence appears in two reviews (dupes survived) | Counted once; distinct source reviews required | `test_QUO_06_duplicate_sentence_sources` | U | P1 |
| QUO-07 | Candidate sentence under 6 or over 22 words | Excluded from selection | `test_QUO_07_length_bounds` | U | P1 |
| QUO-08 | Sentence-splitting traps: "Rs. 5000", "e.g.", "approx.", "No.1 app", decimals "4.5" | Not split incorrectly; quotes are not cut mid-token | `test_QUO_08_sentence_split_traps` | U | P1 |
| QUO-09 | Quote contains profanity or abusive language | Excluded by default (configurable) | `test_QUO_09_profanity_excluded` | U | P1 |
| QUO-10 | Quote names a competitor, a specific employee, or contains accusations of fraud/legal claims | Flagged for exclusion by default; policy documented | `test_QUO_10_sensitive_claims_excluded` | U | P1 |
| QUO-11 | Quote contains curly quotes/apostrophes or emoji | Preserved or normalized consistently; verbatim check uses normalization from §1 | `test_QUO_11_punctuation_and_emoji` | U | P1 |
| QUO-12 | Quote contains `[REDACTED]` | Excluded | `test_QUO_12_redacted_excluded` | U | P0 |
| QUO-13 | Ellipsis joining fragments from different reviews | Rejected | `test_QUO_13_cross_review_ellipsis_rejected` | U | P0 |
| QUO-14 | Non-English-only candidates in top themes | Not selected by default; if config allows, verbatim original script preserved | `test_QUO_14_non_english_policy` | U | P1 |
| QUO-15 | Quote's theme differs from the top 3 | Not allowed unless fallback rule used and recorded | `test_QUO_15_quote_theme_alignment` | U | P1 |
| QUO-16 | Source review later removed during dedupe/retention between selection and validation | Validator detects missing source; blocks | `test_QUO_16_source_missing_blocks` | I | P1 |
| QUO-17 | Quote spans markdown-sensitive characters (`*`, `_`, `>`, backticks) | Escaped in Markdown render; verbatim check on the unescaped text | `test_QUO_17_markdown_escaping` | U | P1 |

---

## 8. Note Generation and Word Budget

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| NOT-01 | Fewer than 3 themes exist | Do **not** pad with fake themes; either publish a note with the available themes and a visible "only N themes" line (policy), or stop. Chosen policy documented; validator rule adjusted accordingly | `test_NOT_01_fewer_than_three_themes` | I | P0 |
| NOT-02 | Rendered note is exactly 250 words | Passes | `test_NOT_02_word_count_250_pass` | U | P0 |
| NOT-03 | Rendered note is 251 words | Fails validation; trigger regeneration/trim | `test_NOT_03_word_count_251_fail` | U | P0 |
| NOT-04 | Word counter edge tokens: `₹5,000`, `4.5★`, `UPI/NEFT`, `e-mail`, URLs, emoji, em-dashes with no spaces | Counted per the §1 definition; counter tested against a table of expected counts | `test_NOT_04_word_counter_table` | U | P0 |
| NOT-05 | Markdown syntax inflating raw character/word counts | Syntax excluded from count | `test_NOT_05_markdown_syntax_excluded` | U | P1 |
| NOT-06 | LLM returns too many actions (4+) or too few (≤2) | Rejected; retry; fail after limit | `test_NOT_06_action_count_exact` | I | P0 |
| NOT-07 | LLM returns actions not tied to a top-3 theme | Rejected | `test_NOT_07_action_theme_grounding` | I | P0 |
| NOT-08 | LLM action text is generic ("improve the app") | Heuristic specificity check (mentions a concrete area/owner/outcome); failing items regenerated | `test_NOT_08_generic_action_rejected` | I | P1 |
| NOT-09 | LLM invents numbers/statistics not in the data | Numbers in summaries must match computed stats; mismatch blocks | `test_NOT_09_invented_numbers_blocked` | I | P0 |
| NOT-10 | LLM claims a root cause ("due to the latest update") not supported by data | Flagged by phrase heuristics ("because of", "due to", "caused by") and requires matching evidence; otherwise rewrite to "users report" | `test_NOT_10_unsupported_causal_claims` | I | P1 |
| NOT-11 | Over-budget after max retries | Deterministic trim of the lowest-priority sentence; re-validate; if still over, fail | `test_NOT_11_trim_fallback` | I | P0 |
| NOT-12 | Theme one-liner exceeds 22 words | Field-level retry | `test_NOT_12_field_budget_enforced` | U | P1 |
| NOT-13 | Note contains non-printing characters or odd Unicode | Normalized; word count stable | `test_NOT_13_unicode_stability` | U | P2 |
| NOT-14 | Window line states wrong store (mentions App Store) | Blocked; note must say "Google Play" only | `test_NOT_14_store_wording_play_only` | U | P1 |
| NOT-15 | Locale/number formatting (percentages, decimals) | Consistent formatting (`12%`, `4.1★`); no locale-dependent output | `test_NOT_15_number_formatting` | U | P2 |
| NOT-16 | Low sample size or short coverage | Note includes a short caveat inside the word budget | `test_NOT_16_caveat_within_budget` | I | P1 |
| NOT-17 | LLM output contains Markdown headings or HTML injection | Rendered through a safe template; unexpected tags stripped | `test_NOT_17_output_sanitized` | U | P1 |
| NOT-18 | Identical input run twice | Structure and facts identical; LLM wording may differ but validator passes both | `test_NOT_18_rerun_validity` | I | P1 |
| NOT-19 | Quote counted in the 250-word budget | Yes: quotes count toward the total | `test_NOT_19_quotes_count_in_budget` | U | P0 |

---

## 9. Validator (fail-closed gate)

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| VAL-01 | Any single check fails (word count, structure, theme cap, verbatim, distinct quotes, PII, grounding) | Overall result = fail; publish stage is not reachable | `test_VAL_01_any_failure_blocks_publish` | I | P0 |
| VAL-02 | Validator crashes (exception) | Treated as fail | `test_VAL_02_validator_exception_fails_closed` | I | P0 |
| VAL-03 | Validator skipped via flag/config | Not possible in publish mode; `--dry-run` only | `test_VAL_03_no_skip_in_publish` | U | P0 |
| VAL-04 | Multiple failures at once | All reported in one readable report | `test_VAL_04_multi_failure_report` | U | P1 |
| VAL-05 | Failure report content | Contains check IDs and counts only; no review text beyond the offending quote index | `test_VAL_05_report_has_no_review_text` | U | P0 |
| VAL-06 | Max regeneration attempts reached | Run ends `failed`; local draft of the note saved with a `FAILED_VALIDATION` marker; nothing published | `test_VAL_06_max_retries_fail` | I | P0 |
| VAL-07 | Validator and renderer disagree on word count | Single shared counter function used by both (enforced by test importing the same module) | `test_VAL_07_single_word_counter` | U | P1 |

---

## 10. MCP Publishing (Docs + Gmail)

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| MCP-01 | Required capability missing (`docs.create` or `gmail.create_draft`) | Fail before any publish step; message names the missing capability | `test_MCP_01_missing_capability_fails_fast` | M | P0 |
| MCP-02 | `docs.update` unsupported | Falls back to versioned doc creation; draft mentions the version | `test_MCP_02_update_unsupported_fallback` | M | P1 |
| MCP-03 | `gmail.update_draft` unsupported | Creates a new draft with a revision suffix; state updated | `test_MCP_03_draft_update_unsupported` | M | P1 |
| MCP-04 | MCP server unreachable / timeout | 3 retries with backoff; then run `failed`; local Markdown saved; actionable message | `test_MCP_04_unreachable_retries_then_fails` | M | P0 |
| MCP-05 | Auth expired/revoked at the MCP host | Clear message ("re-authorize the connector"); no credential prompts in app; no crash loop | `test_MCP_05_auth_expired_message` | M | P1 |
| MCP-06 | Docs succeeds, Gmail fails | State saved with `doc_id`; rerun resumes at Gmail only; no second Doc | `test_MCP_06_partial_failure_resume` | M | P0 |
| MCP-07 | Gmail succeeds but state write fails | Next run detects an existing draft (by stored ID, else by subject search if supported) rather than creating a duplicate; if detection impossible, logs a warning and creates a clearly marked revision | `test_MCP_07_state_write_failure` | M | P1 |
| MCP-08 | Same week, same content hash | No-op; no MCP create/update calls made | `test_MCP_08_same_hash_noop` | M | P0 |
| MCP-09 | Same week, changed content | Updates the existing Doc/draft in place (or versions) | `test_MCP_09_changed_content_update` | M | P0 |
| MCP-10 | Doc deleted manually by the user after publishing | Update call fails "not found" → create a new Doc, update state, note in run report | `test_MCP_10_doc_deleted_externally` | M | P1 |
| MCP-11 | Draft deleted or already sent by the user | Same handling; **never** assumes sent state; creates a new draft | `test_MCP_11_draft_deleted_or_sent` | M | P1 |
| MCP-12 | Tool schema differs (renamed args, extra required args) | Capability resolver adapts via mapping; unknown required args produce a clear config error | `test_MCP_12_schema_drift` | M | P1 |
| MCP-13 | Tool returns success but malformed/empty result (no ID/URL) | Treated as failure | `test_MCP_13_malformed_success_response` | M | P0 |
| MCP-14 | Rate-limit response from the MCP server | Backoff and retry respecting hints; bounded | `test_MCP_14_rate_limit` | M | P1 |
| MCP-15 | Recipient address missing or malformed in config | Config validation error before any call | `test_MCP_15_recipient_validation` | U | P0 |
| MCP-16 | Recipient is an external address (not self/alias) | Warn/block per config (draft should target self or an alias) | `test_MCP_16_external_recipient_guard` | U | P1 |
| MCP-17 | Any attempt to call a "send" tool | Impossible: send capabilities are not in the allowed capability map; test asserts the code path doesn't exist | `test_MCP_17_no_send_capability` | U | P0 |
| MCP-18 | Static scan of codebase | No imports of Google API client libraries, OAuth libs for Google, or direct `googleapis.com` URLs | `test_MCP_18_no_google_sdk_or_rest` | U | P0 |
| MCP-19 | Doc body formatting: quotes with special characters, long lines, Markdown conversion | Renders correctly; no raw Markdown artifacts if the server needs plain text/HTML | `test_MCP_19_doc_formatting` | S | P1 |
| MCP-20 | Email body: HTML vs plain-text support differs by server | Falls back to plain text; content identical | `test_MCP_20_email_format_fallback` | M | P2 |
| MCP-21 | Email body length/encoding with Unicode (₹, ★, Devanagari quotes if allowed) | Preserved; subject uses safe characters | `test_MCP_21_unicode_in_email` | M | P1 |
| MCP-22 | Concurrent runs for the same week (two processes) | Lock prevents duplicate publish; second run exits with a message | `test_MCP_22_concurrent_run_lock` | I | P1 |
| MCP-23 | MCP call is slow (> timeout) but eventually succeeds | Timeout handled; retry doesn't create duplicate objects (idempotency check by state/ID) | `test_MCP_23_slow_success_no_duplicate` | M | P1 |
| MCP-24 | Pre-publish PII gate on subject and body just before the draft call | Re-scan occurs; seeded PII blocks the call | `test_MCP_24_email_pii_gate` | M | P0 |
| MCP-25 | Doc link inserted into the email | Uses the returned `doc_url`; if missing, email states "Doc link unavailable" and run flags a warning | `test_MCP_25_doc_link_in_email` | M | P1 |
| MCP-26 | Doc title/subject contain the week date | Correct ISO week-start date; consistent across Doc, draft, and state | `test_MCP_26_title_subject_consistency` | U | P1 |

---

## 11. Configuration and Environment

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| CFG-01 | `max_themes` > 5 in config | Rejected at startup (hard cap is 5) | `test_CFG_01_theme_cap_hard_limit` | U | P0 |
| CFG-02 | `max_words` > 250 | Rejected at startup | `test_CFG_02_word_cap_hard_limit` | U | P0 |
| CFG-03 | `quotes` ≠ 3 or `actions` ≠ 3 | Rejected (project requires exactly 3) | `test_CFG_03_counts_fixed` | U | P0 |
| CFG-04 | Missing config file / invalid YAML | Clear error; exit non-zero | `test_CFG_04_invalid_config` | U | P1 |
| CFG-05 | Secrets (LLM API key) missing | Clear error naming the env var; never prints the key value | `test_CFG_05_missing_secret_message` | U | P1 |
| CFG-06 | Secrets present: ensure never logged or written to outputs | Logs/outputs scanned for key patterns | `test_CFG_06_no_secrets_in_outputs` | I | P0 |
| CFG-07 | Unknown config keys | Warn, don't crash (or strict mode errors) | `test_CFG_07_unknown_keys` | U | P2 |
| CFG-08 | `.gitignore` covers `data/`, `outputs/`, `.env` | Verified by a repo check | `test_CFG_08_gitignore_protects_data` | U | P1 |
| CFG-09 | Different working directory / Windows path separators (project lives on Windows paths such as `D:\...`) | Paths handled via `pathlib`; tests run on Windows and POSIX | `test_CFG_09_cross_platform_paths` | U | P1 |

---

## 12. Orchestration, State, and Scheduling

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| ORC-01 | `--dry-run` | Runs through validation; no MCP calls; no `publish_state` changes | `test_ORC_01_dry_run_no_side_effects` | I | P0 |
| ORC-02 | `--stage` resume from cached intermediates | Skips earlier stages; results identical to a full run | `test_ORC_02_stage_resume` | I | P1 |
| ORC-03 | Crash mid-run (kill after clustering) | `runs.status` stays `running`/`failed`; rerun recovers cleanly; no half-written rows | `test_ORC_03_crash_recovery` | I | P1 |
| ORC-04 | SQLite file locked or corrupted | Clear error; no partial publish | `test_ORC_04_db_failure` | I | P1 |
| ORC-05 | Disk full when writing outputs | Error surfaced; no publish | `test_ORC_05_disk_full` | I | P2 |
| ORC-06 | Scheduler fires twice for the same week | Second run no-ops (same hash) or is blocked by lock | `test_ORC_06_double_trigger` | I | P1 |
| ORC-07 | Scheduler missed a week; run later with `--week` for the past | Works for past weeks within available data; labeled accordingly | `test_ORC_07_backfill_week` | I | P2 |
| ORC-08 | Retention purge runs while a run is active | Purge never deletes rows used by an active run | `test_ORC_08_purge_vs_active_run` | I | P1 |
| ORC-09 | Retention removes old raw files | Only files outside window + one prior window removed | `test_ORC_09_retention_scope` | U | P2 |
| ORC-10 | Run report generation | Contains counts and statuses; passes PII scan | `test_ORC_10_run_report_clean` | I | P0 |
| ORC-11 | Exit codes | 0 on success/no-op, non-zero on failure, distinct code for "validation failed" | `test_ORC_11_exit_codes` | U | P1 |
| ORC-12 | Clock/timezone of the scheduler host differs (IST vs UTC) | `week_start` resolved in UTC consistently | `test_ORC_12_timezone_consistency` | U | P1 |

---

## 13. Security, Privacy, and Compliance

| ID | Scenario | Expected | Test | Type | Pri |
|---|---|---|---|---|---|
| SEC-01 | Repository search for identity field names in stored data | None present | `test_SEC_01_no_identity_fields_stored` | I | P0 |
| SEC-02 | Fixtures/sample outputs committed to the repo | Contain only synthetic data and are labeled as such | `test_SEC_02_fixtures_labeled_synthetic` | U | P1 |
| SEC-03 | Third-party telemetry/analytics in dependencies sending data externally | None enabled; embedding model runs locally or via the approved provider only | `test_SEC_03_no_unapproved_egress` | I | P1 |
| SEC-04 | Network calls during tests | Blocked by default (use mocks); test fails on any unmocked network call | `test_SEC_04_network_blocked_in_tests` | I | P1 |
| SEC-05 | Automated collection from Play disabled unless a recorded approval exists | Verified by config guard (see ING-14) | `test_SEC_05_automation_guard` | U | P0 |
| SEC-06 | Output paths | Written only inside `outputs/` and `data/`; no path traversal via `--week` or config | `test_SEC_06_path_traversal` | U | P1 |
| SEC-07 | Dependency versions pinned and audited | Lockfile present; audit step runs in CI | `test_SEC_07_lockfile_present` | U | P2 |

---

## 14. Cross-Cutting Invariants (property tests, run on every phase)

These must hold for **any** valid or invalid input. AG should implement them once as reusable assertions and call them from end-to-end tests.

```python
# tests/invariants.py  (sketch for AG)
def assert_note_invariants(note, dataset, config):
    assert len({t.label for t in note.all_themes}) <= 5               # theme cap
    assert len(note.top_themes) == 3 or note.policy_allows_fewer      # top 3 (see NOT-01)
    assert len(note.quotes) == 3
    assert len({q.source_review_id for q in note.quotes}) == 3        # distinct reviews
    for q in note.quotes:
        assert is_verbatim(q.text, dataset[q.source_review_id].text)  # verbatim
        assert "[REDACTED]" not in q.text
    assert len(note.actions) == 3
    assert all(a.theme in note.top_theme_labels for a in note.actions)
    assert count_words(render(note)) <= 250                            # shared counter
    assert not pii_scan(render(note))                                  # no PII
    assert "App Store" not in render(note)                             # Play-only scope

def assert_pipeline_invariants(run):
    if run.status != "validated":
        assert run.mcp_calls == []                                     # fail closed
    assert not any(tool.is_send for tool in run.mcp_calls)             # never send
    assert not pii_scan(run.log_text + run.report_text)                # clean logs/reports
```

| ID | Invariant | Test | Pri |
|---|---|---|---|
| INV-01 | Note invariants hold across 200 randomized fixture datasets (varying size, language mix, PII density, rating skew) | `test_INV_01_note_invariants_randomized` | P0 |
| INV-02 | Pipeline never calls MCP when validation fails | `test_INV_02_no_mcp_on_failure` | P0 |
| INV-03 | Rerun with identical inputs is idempotent (state, Doc count, draft count) | `test_INV_03_idempotent_rerun` | P0 |
| INV-04 | Seeded canary strings (fake PII) never appear in any artifact | `test_INV_04_canary_strings_absent` | P0 |

---

## 15. Required Fixtures (AG to create under `tests/fixtures/`)

| Fixture | Purpose | Contents |
|---|---|---|
| `reviews_baseline.csv` | Happy-path run | ~250 synthetic reviews across KYC, payments/UPI, withdrawals, crashes/login, charges, support, positive UX; 8-12 week spread |
| `reviews_pii_heavy.csv` | PII tests | Every PII type in §5.1 across text and title; sign-offs; obfuscated emails; Unicode digits |
| `reviews_pii_negatives.csv` | Over-redaction guards | Items from §5.2 |
| `reviews_low_info.csv` | Low-info and spam | Emoji-only, one-word, bursts of duplicates |
| `reviews_multilingual.csv` | Language handling | English, Hindi, Hinglish, code-mixed, unknown |
| `reviews_tiny.csv` | Small-sample paths | 0, 1, 2, 9, 10 reviews variants |
| `reviews_spike.csv` | Outage spike | One theme at >60% share |
| `reviews_identity_columns.csv` | ING-01 | Includes fake name/user-id/avatar/device columns |
| `reviews_bad_formats.csv` | Parsing | Mixed date formats, bad ratings, broken quoting, BOM |
| `reviews_injection.csv` | LLM safety | Reviews containing prompt-injection strings |
| `mock_mcp_server/` | MCP contract tests | Configurable behaviors: success, timeout, auth error, missing capability, malformed response, partial failure, rate limit, not-found |
| `canaries.json` | INV-04 | List of unique fake PII strings seeded into fixtures |

---

## 16. Execution Order for AG (aligned to `implementation-plan.md`)

| Phase | Required test groups (P0 first, then P1, then P2) |
|---|---|
| **0: Foundations** | CFG-01..09, ING-14, ING-15, MCP-17, MCP-18, SEC-04; MCP spike notes feed MCP-12 |
| **1: Ingestion + PII** | ING-*, WIN-*, NRM-*, LNG-*, DUP-*, LOW-*, PII-01..20, PIIN-*, PII-30..39, SEC-01..03 |
| **2: Themes** | THM-*, LBL-*, INV for theme cap |
| **3: Note + Validation** | QUO-*, NOT-*, VAL-*, INV-01, INV-04 |
| **4: MCP Publish** | MCP-*, INV-02, INV-03 |
| **5: Orchestration** | ORC-*, SEC-05..07, INV-* across end-to-end |
| **6: Acceptance** | Full suite green; manual smoke tests MCP-19; acceptance checklist in `implementation-plan.md` |

**Gate rule:** a phase is complete only when all its **P0** tests pass and all **P1** failures are either fixed or logged in `docs/known-issues.md` with an owner and a reason.

---

## 17. Manual Smoke Checklist (real MCP connectors, personal/sandbox account)

- [ ] Run `pulse run --week <date>` once: one Doc and one draft appear; the draft is **unsent**.
- [ ] Open the Doc: headings, bullets, and quotes render cleanly; word count ≤ 250.
- [ ] Open the draft: recipient is the configured self/alias; body matches the note; Doc link opens.
- [ ] Run the same command again: no new Doc, no new draft (or clearly marked version).
- [ ] Change one input review, re-run: Doc and draft update in place.
- [ ] Delete the draft manually, re-run: a fresh draft is created, Doc untouched.
- [ ] Search the Doc, draft, and `outputs/` for the canary strings: zero hits.
- [ ] Disconnect the MCP connector, re-run: clear failure message; local Markdown preserved.

---

## 18. Open Decisions That Affect These Tests

| Decision | Affects | Default assumed in this file |
|---|---|---|
| Behavior when fewer than 3 themes exist | NOT-01, VAL, THM-04 | Publish with the available themes and a visible caveat; never invent themes |
| Whether non-English quotes are allowed | QUO-14, LNG-* | Not allowed by default |
| Positive-theme dominance policy | THM-15 | At least one issue-oriented theme in top 3 when one exists above min share |
| Near-duplicate threshold and short-generic-review policy | DUP-03, DUP-04 | Configurable; defaults set in `config/pulse.yaml` |
| Update vs create-only MCP behavior | MCP-02, MCP-03, MCP-09 | Prefer in-place update; fall back to versioning |
| Recipient restrictions | MCP-16 | Self or alias only |
| Profanity/sensitive-claim policy in quotes | QUO-09, QUO-10 | Exclude by default |

AG should update this table and the affected tests whenever a decision changes.
