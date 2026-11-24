import os

import numpy as np
import pytest

from src.pipeline import run_full_pipeline, run_themes_stage
from src.store.factory import postgres_store, sqlite_store
from src.store.models import ReviewRecord
from src.themes.embed import VECTOR_SIZE, embed_reviews
from tests.test_phase7_store import BACKENDS, POSTGRES_DSN_ENV, _fresh_postgres_dsn
from tests.test_pulse_status import CSV, WEEK

TOPICS = (
    ("charges brokerage fees deducted hidden account money", 1),
    ("login easy clean simple interface smooth investing", 5),
    ("support ticket reply waiting agent chat unresolved", 2),
    ("chart crash market order slow freeze trading", 1),
)
DATES = tuple(f"2026-{month}-{day:02d}" for month in ("09", "10") for day in range(1, 29))
STORED_EARLIER = 180


def _reviews(count):
    rng = np.random.default_rng(7)
    vocabulary = [word for topic, _ in TOPICS for word in topic.split()]
    reviews = []
    for n in range(count):
        topic, rating = TOPICS[rng.integers(len(TOPICS))]
        words = list(rng.choice(topic.split(), 5, replace=False)) + list(rng.choice(vocabulary, 6))
        reviews.append(ReviewRecord(
            f"rev-{n:04d}", "play_store", rating, " ".join(words), DATES[rng.integers(len(DATES))], lang="en"))
    return reviews


@pytest.fixture(params=BACKENDS)
def stores(request, tmp_path):
    def new(name):
        if request.param == "sqlite":
            return sqlite_store(tmp_path / f"{name}.db").for_app("groww")
        if POSTGRES_DSN_ENV not in os.environ:
            pytest.skip(f"{POSTGRES_DSN_ENV} is not set")
        return postgres_store(_fresh_postgres_dsn()).for_app("groww")

    return new


def _themes(store, run_id):
    run_themes_stage(store, WEEK, run_id=run_id)
    members = {t: [r.review_id for r in reviews] for t, reviews in store.get_theme_reviews(run_id).items()}
    return [(t.theme_id, t.label, t.share_pct, t.avg_rating, members[t.theme_id]) for t in store.get_themes(run_id)]


def test_rerun_on_the_same_reviews_gives_the_same_themes(stores):
    reviews = _reviews(240)
    store = stores("history")
    store.upsert_reviews(reviews[:STORED_EARLIER])
    _themes(store, "earlier")
    store.upsert_reviews(reviews[STORED_EARLIER:])
    assert _themes(store, "first") == _themes(store, "again")


def test_themes_do_not_depend_on_when_reviews_arrived(stores):
    reviews = _reviews(240)
    history, at_once = stores("history"), stores("at_once")
    for end in (60, STORED_EARLIER, len(reviews)):
        history.upsert_reviews(reviews[:end])
        _themes(history, f"run-{end}")
    at_once.upsert_reviews(reversed(reviews))
    assert _themes(history, "last") == _themes(at_once, "only")


def test_rerun_after_new_reviews_leaves_the_doc_and_draft_alone(stores, composio, tmp_path):
    store = stores("published")
    rows = CSV.read_text(encoding="utf-8").splitlines(keepends=True)
    earlier = tmp_path / "earlier.csv"
    earlier.write_text("".join(rows[:151]), encoding="utf-8")
    run_full_pipeline(store, WEEK, csv_path=earlier, mcp_client=composio.client())
    run_full_pipeline(store, WEEK, csv_path=CSV, mcp_client=composio.client())
    published = store.get_publish_state(WEEK)
    run_full_pipeline(store, WEEK, csv_path=CSV, mcp_client=composio.client())
    assert store.get_publish_state(WEEK) == published


def test_themes_with_equal_shares_come_back_in_one_order(stores):
    store = stores("ties")
    themes = [{"theme_id": theme_id, "label": theme_id, "description": "d", "review_count": 1, "share_pct": 0.5,
               "avg_rating": 3.0, "neg_share": 0.0, "priority_score": 0.0, "is_top3": 1, "member_review_ids": []}
              for theme_id in ("thm_b", "thm_a")]
    store.save_theme_run(
        run_id="ties", week_start=WEEK, window_start=WEEK, window_end=WEEK, total_reviews=2, analyzed_reviews=2,
        avg_rating=3.0, coverage_weeks=1.0, themes=themes)
    assert [t.theme_id for t in store.get_themes("ties")] == ["thm_a", "thm_b"]


def test_vectors_need_only_the_reviews():
    reviews = _reviews(120)
    assert np.array_equal(embed_reviews(reviews), embed_reviews(reviews))
    assert embed_reviews(reviews[:20]).shape[0] == 20
    assert embed_reviews([]).shape == (0, VECTOR_SIZE)
