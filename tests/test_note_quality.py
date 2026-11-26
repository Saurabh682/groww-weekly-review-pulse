import pytest

from src.domains import FINANCE_PACK, GENERIC_PACK
from src.note.fit import fits_theme
from src.note.generate import synthesize_action_items
from src.note.models import ActionItem, Quote, StoreCoverage, ThemeSummary, WeeklyPulseNote
from src.note.render import render_html, render_markdown, render_plain_text
from src.note.select import select_quotes_for_themes
from src.note.validate import STATUS_QUO_ACTION as STATUS_QUO, validate_note
from src.store.models import ReviewRecord, ThemeRecord

PACKS = [FINANCE_PACK, GENERIC_PACK]


def _theme(theme_id: str, label: str, avg: float = 1.5) -> ThemeRecord:
    return ThemeRecord(
        theme_id=theme_id, run_id="r", label=label, description="d", review_count=10,
        share_pct=0.3, avg_rating=avg, is_top3=True, neg_share=0.5, priority_score=1.0,
    )


def _review(review_id: str, text: str, rating: int = 1) -> ReviewRecord:
    return ReviewRecord(
        review_id=review_id, platform="play_store", rating=rating, text=text, date="2026-11-01",
        lang="en", low_info=0, pii_found=0, quote_eligible=1, raw_hash=review_id,
    )


def test_QUO_18_a_quote_names_what_its_theme_is_about():
    assert fits_theme("The brokerage charge on every intraday order is far too high", "Charges & Pricing", FINANCE_PACK)
    assert not fits_theme(
        "The money has been deducted from my bank account 10 days back, the wallet is still not credited",
        "Charges & Pricing",
        FINANCE_PACK,
    )
    assert not fits_theme(
        "I requested a withdrawal on 8 October, but my funds have still not been credited",
        "Customer Support",
        FINANCE_PACK,
    )


def test_QUO_18_labels_outside_the_pack_match_their_own_words():
    assert fits_theme("Food delivery was late again and the delivery partner never called", "Delivery & Partner", FINANCE_PACK)
    assert not fits_theme("The app keeps crashing whenever I open the portfolio screen", "Delivery & Partner", FINANCE_PACK)


def test_QUO_18_selection_skips_a_sentence_about_another_theme():
    charges = _theme("t1", "Charges & Pricing")
    reviews = {
        "t1": [
            _review("a", "The money has been deducted from my bank account 10 days back, the wallet is still not credited"),
            _review("b", "They took a hidden brokerage charge on my delivery order without telling me"),
        ]
    }
    quotes = select_quotes_for_themes([charges], reviews, FINANCE_PACK, max_quotes=1)
    assert [q.source_review_id for q in quotes] == ["b"]


@pytest.mark.parametrize("pack", PACKS, ids=lambda p: p.name)
def test_NOT_20_every_pack_label_has_its_own_action(pack):
    assert sorted(pack.label_keywords) == sorted(pack.actions), (
        "Every theme label a pack can produce needs an action blueprint under the same key."
    )


@pytest.mark.parametrize("pack", PACKS, ids=lambda p: p.name)
def test_NOT_20_pack_actions_change_something(pack):
    assert [k for k, a in pack.actions.items() if STATUS_QUO.match(a.text)] == []


def test_NOT_20_fallback_actions_change_something():
    themes = [_theme("t1", "Delivery & Partner", 1.8), _theme("t2", "Rewards & Cashback", 4.4), _theme("t3", "Food Quality", 3.1)]
    actions = synthesize_action_items(themes, GENERIC_PACK)
    assert [a.text for a in actions if STATUS_QUO.match(a.text)] == []


def _note(actions):
    themes = [
        ThemeSummary(f"t{i}", label, "d", "one liner here", 10, 0.3, 2.0, 0.5)
        for i, label in enumerate(["Charges & Pricing", "Customer Support", "Positive UX & Simplicity"], 1)
    ]
    quotes = [
        Quote("They took a hidden brokerage charge on my order", "a", 1, "Charges & Pricing", "2026-11-01"),
        Quote("Support never replied to my ticket for two weeks", "b", 1, "Customer Support", "2026-11-01"),
        Quote("Very easy and simple app to start investing in", "c", 5, "Positive UX & Simplicity", "2026-11-01"),
    ]
    return WeeklyPulseNote(
        week_start="2026-11-16", window_start="2026-08-31", window_end="2026-11-22", app_name="Groww",
        store_coverage=[StoreCoverage("play_store", 8000)], total_reviews=8000, analyzed_reviews=1799,
        avg_rating=4.2, top_themes=themes, quotes=quotes, actions=actions,
    )


def test_NOT_20_validator_rejects_a_status_quo_action():
    actions = [
        ActionItem("Charges & Pricing", "Show an itemised fee breakdown on every order confirmation screen."),
        ActionItem("Customer Support", "Route unresolved payment tickets older than 48 hours to a priority queue."),
        ActionItem("Positive UX & Simplicity", "Maintain current simplified mutual fund dashboard layout for users."),
    ]
    note = _note(actions)
    errors = validate_note(note, render_markdown(note)).errors
    assert any("NOT-20" in e for e in errors), errors


def test_NOT_21_header_rating_says_it_covers_every_review():
    note = _note([])
    for rendered in (render_markdown(note), render_html(note), render_plain_text(note)):
        assert "Avg rating 4.2★ (all reviews)" in rendered
        assert "Themes from 1,799 detailed reviews" in rendered
