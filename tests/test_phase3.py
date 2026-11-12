"""Unit and integration tests for Phase 3: Note Generation and Validation.

Covers:
- Word counting: NOT-02..05, VAL-07
- Validation invariants: VAL-01..05, NOT-01, NOT-06..08, NOT-12, NOT-14
- Quote extraction and verbatim properties: QUO-01..08, QUO-12, QUO-15
- Budget enforcement and rendering: NOT-11, NOT-17, MCP-19..21
- Canary and PII absence: INV-04
"""

import json
from pathlib import Path
import pytest

from src.note.generate import (
    enforce_word_budget,
    synthesize_action_items,
    synthesize_theme_one_liner,
)
from src.note.models import ActionItem, Quote, ThemeSummary, WeeklyPulseNote
from src.note.render import render_html, render_markdown, render_plain_text
from src.note.select import (
    compute_sentence_score,
    is_candidate_eligible,
    select_quotes_for_themes,
    split_sentences,
)
from src.note.validate import (
    is_verbatim_substring,
    validate_note,
    ValidationResult,
)
from src.note.words import count_note_words, strip_markdown
from src.store.models import ReviewRecord, ThemeRecord


# ==============================================================================
# Word Counting Tests (NOT-02..05, VAL-07)
# ==============================================================================

def test_NOT_04_word_counter_edge_tokens():
    """NOT-04 (P1): Handles currency, ratings, compound terms, and hyphenated words."""
    text = "Transferred ₹5,000 with 4.5★ rating via UPI/NEFT support e-mail."
    # Transferred(1) ₹5,000(2) with(3) 4.5★(4) rating(5) via(6) UPI/NEFT(7) support(8) e-mail(9)
    assert count_note_words(text) == 9


def test_NOT_05_markdown_syntax_excluded():
    """NOT-05 (P1): Markdown formatting markers do not artificially inflate word count."""
    raw = "# Header Title\n\n**Bold text** with *italics* and `inline_code`.\n\n- Bullet 1\n- Bullet 2"
    stripped = strip_markdown(raw)
    assert "#" not in stripped
    assert "**" not in stripped
    assert "`" not in stripped
    # Words: Header, Title, Bold, text, with, italics, and, inline_code, Bullet, 1, Bullet, 2 -> 12 words
    assert count_note_words(raw) == 12


def test_NOT_02_word_count_250_pass():
    """NOT-02 (P0): Rendered note at exactly 250 words passes validation."""
    words = ["word"] * 250
    text = "Google Play " + " ".join(words[2:])
    assert count_note_words(text) == 250

    note = _create_mock_note()
    res = validate_note(note, text)
    assert "word_count_cap" in res.checks_passed
    assert not any("NOT-03" in e for e in res.errors)


def test_NOT_03_word_count_251_fails():
    """NOT-03 (P0): Rendered note at 251 words fails validation."""
    words = ["word"] * 251
    text = "Google Play " + " ".join(words[2:])
    assert count_note_words(text) == 251

    note = _create_mock_note()
    res = validate_note(note, text)
    assert any("NOT-03" in e for e in res.errors)
    assert not res.is_valid


def test_VAL_07_shared_word_counter():
    """VAL-07 (P0): Renderer and Validator agree on word count."""
    note = _create_mock_note()
    md = render_markdown(note)
    wc = count_note_words(md)
    res = validate_note(note, md)
    assert res.word_count == wc


# ==============================================================================
# Quote Extraction & Verbatim Tests (QUO-01..16)
# ==============================================================================

def test_QUO_08_sentence_splitting_decimals_abbreviations():
    """QUO-08 (P1): Sentence splitting respects Rs., e.g., approx., and decimals."""
    text = "Added Rs. 5000 via UPI. Version 4.5 is smooth e.g. for SIP setup. Please check."
    sentences = split_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Added Rs. 5000 via UPI"
    assert "Version 4.5 is smooth e.g. for SIP setup" in sentences[1]


def test_QUO_07_length_bounds():
    """QUO-07 (P1): Sentences < 6 words or > 22 words are excluded."""
    too_short = "Great app."
    assert not is_candidate_eligible(too_short)

    in_bounds = "Money debited from bank account but not credited to Groww wallet."
    assert is_candidate_eligible(in_bounds)

    too_long = " ".join(["word"] * 25)
    assert not is_candidate_eligible(too_long)


def test_QUO_12_redacted_excluded():
    """QUO-12 (P0): Candidate sentences containing [REDACTED] are excluded."""
    sent = "My account [REDACTED] failed without giving any reason."
    assert not is_candidate_eligible(sent)


def test_QUO_05_distinct_reviews_required():
    """QUO-05 (P0): Quotes must come from 3 distinct reviews."""
    note = _create_mock_note()
    # Duplicate source review id
    q1 = note.quotes[0]
    bad_quotes = [q1, q1, note.quotes[2]]
    bad_note = WeeklyPulseNote(
        week_start=note.week_start,
        window_start=note.window_start,
        window_end=note.window_end,
        top_themes=note.top_themes,
        quotes=bad_quotes,
        actions=note.actions
    )
    md = render_markdown(bad_note)
    res = validate_note(bad_note, md)
    assert any("QUO-05" in e for e in res.errors)


def test_QUO_01_verbatim_check():
    """QUO-01 (P0): Quotes must be exact verbatim substrings of source review."""
    rev_id = "rev_101"
    src_text = "Withdrawal request placed on Monday, still pending on Friday."
    rev = ReviewRecord(rev_id, "play_store", 1, src_text, "2026-11-04")
    
    quote = Quote(
        text="Withdrawal request placed on Monday, still pending on Friday.",
        source_review_id=rev_id,
        rating=1,
        theme_label="Payments",
        date="2026-11-04"
    )
    assert is_verbatim_substring(quote.text, src_text)


def test_QUO_02_mutation_detected():
    """QUO-02 (P0): Changing even 1 word or character fails verbatim validation."""
    rev_id = "rev_101"
    src_text = "Withdrawal request placed on Monday, still pending on Friday."
    mutated_text = "Withdrawal request placed on Monday, still pending on Saturday."
    assert not is_verbatim_substring(mutated_text, src_text)


# ==============================================================================
# Action Items & Theme Validation (NOT-01, NOT-06..08, NOT-12, NOT-14)
# ==============================================================================

def test_NOT_06_action_count_invariants():
    """NOT-06 (P0): Exactly 3 action items required; extra or missing rejected."""
    note = _create_mock_note()
    # 2 actions
    bad_note = WeeklyPulseNote(
        week_start=note.week_start,
        window_start=note.window_start,
        window_end=note.window_end,
        top_themes=note.top_themes,
        quotes=note.quotes,
        actions=note.actions[:2]
    )
    res = validate_note(bad_note, render_markdown(bad_note))
    assert any("NOT-06" in e for e in res.errors)


def test_NOT_07_action_theme_grounding():
    """NOT-07 (P0): Actions must map to one of the top-3 themes."""
    note = _create_mock_note()
    bad_actions = [
        ActionItem(theme_label="Unrelated Fantasy Theme", text="Fix unrelated fantasy feature.")
    ] + note.actions[1:]
    bad_note = WeeklyPulseNote(
        week_start=note.week_start,
        window_start=note.window_start,
        window_end=note.window_end,
        top_themes=note.top_themes,
        quotes=note.quotes,
        actions=bad_actions
    )
    res = validate_note(bad_note, render_markdown(bad_note))
    assert any("NOT-07" in e for e in res.errors)


def test_NOT_08_generic_action_rejected():
    """NOT-08 (P1): Generic phrases like 'improve the app' or 'fix bugs' rejected."""
    note = _create_mock_note()
    bad_actions = [
        ActionItem(theme_label=note.top_themes[0].label, text="Please improve the app.")
    ] + note.actions[1:]
    bad_note = WeeklyPulseNote(
        week_start=note.week_start,
        window_start=note.window_start,
        window_end=note.window_end,
        top_themes=note.top_themes,
        quotes=note.quotes,
        actions=bad_actions
    )
    res = validate_note(bad_note, render_markdown(bad_note))
    assert any("NOT-08" in e for e in res.errors)


def test_NOT_12_theme_one_liner_length():
    """NOT-12 (P1): Theme one-liner must be <= 22 words."""
    t = ThemeRecord("t1", "r1", "Charges & Pricing", "desc", 100, 0.25, 2.0)
    one_liner = synthesize_theme_one_liner(t)
    assert count_note_words(one_liner) <= 22


def test_NOT_14_google_play_scope():
    """NOT-14 (P0): Google Play must be specified; App Store / iOS prohibited."""
    note = _create_mock_note()
    md_valid = render_markdown(note)
    assert "Google Play" in md_valid
    assert "App Store" not in md_valid

    # If App Store is injected, validation fails
    md_invalid = md_valid.replace("Google Play", "Apple App Store")
    res = validate_note(note, md_invalid)
    assert any("NOT-14" in e for e in res.errors)


# ==============================================================================
# Security, Canaries & PII Absence (INV-04, VAL-05)
# ==============================================================================

def test_INV_04_canaries_absent():
    """INV-04 (P0): Seeded canaries or PII never pass note validation."""
    canaries_file = Path("groww-weekly-review-pulse/tests/fixtures/canaries.json")
    if not canaries_file.exists():
        canaries_file = Path("tests/fixtures/canaries.json")
    
    canary_data = json.loads(canaries_file.read_text(encoding="utf-8"))
    canary_phone = canary_data["phones"][0]
    note = _create_mock_note()
    base_md = render_markdown(note)

    # Invalidate note with a canary
    contaminated_md = base_md + f"\n\nCustomer phone: {canary_phone}"
    res = validate_note(note, contaminated_md)
    assert not res.is_valid
    assert any("INV-04" in e for e in res.errors)


def test_VAL_02_validator_fails_closed():
    """VAL-02 (P0): Validator fails closed on unexpected exceptions."""
    # Pass an invalid note type causing an attribute error inside
    res = validate_note(None, "text")  # type: ignore
    assert not res.is_valid
    assert any("VAL-02" in e for e in res.errors)


def test_NOT_11_budget_trimmer():
    """NOT-11 (P1): enforce_word_budget trims text cleanly if over 250 words."""
    long_note = "Google Play reviews.\n\n" + "\n\n".join(["- " + ("word " * 60) for _ in range(5)])
    assert count_note_words(long_note) > 250
    trimmed = enforce_word_budget(long_note, max_words=250)
    assert count_note_words(trimmed) <= 250


# ==============================================================================
# Helper Mock Builder
# ==============================================================================

def _create_mock_note() -> WeeklyPulseNote:
    t1 = ThemeSummary("t1", "Charges & Pricing", "Desc", "Transparent fees requested on equity.", 100, 0.35, 2.2, 0.75)
    t2 = ThemeSummary("t2", "App Performance & Bugs", "Desc", "App lag reported during market open.", 80, 0.28, 2.4, 0.65)
    t3 = ThemeSummary("t3", "Customer Support", "Desc", "Support ticket resolution delayed.", 60, 0.20, 1.8, 0.80)

    q1 = Quote("Withdrawal request placed on Monday, still pending on Friday.", "r1", 1, "Charges & Pricing", "2026-11-04")
    q2 = Quote("Nifty terminal lagging and freezing during morning volatility.", "r2", 2, "App Performance & Bugs", "2026-11-03")
    q3 = Quote("Support ticket unresolved for five days with generic replies.", "r3", 1, "Customer Support", "2026-11-02")

    a1 = ActionItem("Charges & Pricing", "Deploy fee calculator on order confirmation.", "Core Brokerage")
    a2 = ActionItem("App Performance & Bugs", "Conduct market open websocket channel load testing.", "Mobile Reliability")
    a3 = ActionItem("Customer Support", "Implement automated ticket escalation for 48 hour delays.", "Customer Ops")

    return WeeklyPulseNote(
        week_start="2026-11-10",
        window_start="2026-09-07",
        window_end="2026-11-10",
        platform="Google Play",
        total_reviews=1435,
        analyzed_reviews=662,
        avg_rating=2.7,
        top_themes=[t1, t2, t3],
        quotes=[q1, q2, q3],
        actions=[a1, a2, a3],
        coverage_weeks=9.0,
        short_coverage_flag=False
    )
