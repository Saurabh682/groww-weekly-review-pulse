import json
import os
import re
import subprocess
import sys

import numpy as np
import pytest

from src.config import PROJECT_ROOT
from src.store.models import ReviewRecord
from src.themes.cluster import cluster_reviews
from src.themes.embed import embed_reviews
from src.themes.label import extract_cluster_keywords
from src.themes.terms import weigh_terms

TOPICS = {
    "charges": "brokerage charges fees deducted account money hidden",
    "login": "login easy clean simple interface smooth investing",
    "support": "support ticket reply waiting agent chat unresolved",
    "orders": "chart crash market order slow freeze trading",
}
REVIEWS_PER_TOPIC = 100
RARE_WORDS_PER_REVIEW = 6
RARE_WORDS = 1500


def reviews():
    rng = np.random.default_rng(3)
    records = []
    for topic, words in TOPICS.items():
        for n in range(REVIEWS_PER_TOPIC):
            rare = [f"rare{w:04d}" for w in rng.integers(RARE_WORDS, size=RARE_WORDS_PER_REVIEW)]
            text = " ".join(list(rng.choice(words.split(), 5, replace=False)) + rare)
            records.append(ReviewRecord(f"{topic}-{n:03d}", "play_store", 3, text, "2026-10-10", lang="en"))
    return records


def grouping():
    records = reviews()
    vectors = embed_reviews(records)
    clusters, _, _ = cluster_reviews(vectors=vectors, reviews=records)
    members = sorted(sorted(records[i].review_id for i in group) for group in clusters.values())
    tied = [f"{word} {word}" for word in ("pear", "fig", "kiwi", "plum", "lime", "date", "sloe", "nut", "yam", "pea")] * 12
    many = [" ".join(f"w{n:03d}" for n in range(start, start + 8)) for start in range(0, 320, 8)]
    return {
        "vectors": np.round(vectors, 4).tolist(), "members": members,
        "keywords": [extract_cluster_keywords(tied), extract_cluster_keywords(many)],
    }


def _grouping_on(disabled):
    env = {**os.environ, "NPY_DISABLE_CPU_FEATURES": " ".join(disabled)}
    script = "import json; from tests.test_stable_terms import grouping; print(json.dumps(grouping()))"
    done = subprocess.run([sys.executable, "-c", script], cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, check=True)
    return json.loads(done.stdout)


@pytest.fixture(scope="module")
def results():
    optional = np.show_config(mode="dicts")["SIMD Extensions"]["found"]
    assert optional, "this machine has no optional CPU features to turn off"
    return _grouping_on([]), _grouping_on(optional)


def test_every_cpu_gives_the_same_vectors(results):
    with_features, without = results
    assert np.allclose(with_features["vectors"], without["vectors"], atol=0.001)


def test_every_cpu_gives_the_same_themes(results):
    with_features, without = results
    assert with_features["members"] == without["members"]


def test_every_cpu_gives_the_same_keywords(results):
    with_features, without = results
    assert with_features["keywords"] == without["keywords"]


def test_tied_keywords_are_taken_alphabetically():
    assert extract_cluster_keywords(["pear", "fig", "kiwi", "plum", "lime", "date"]) == ["Date", "Fig", "Kiwi", "Lime", "Pear"]


def test_only_the_most_used_terms_are_weighed():
    weights, terms = weigh_terms(["apple banana cherry", "banana cherry", "cherry"], 2)
    assert list(terms) == ["banana", "cherry"]
    assert weights.shape == (3, 2)
    assert list(weights.toarray()[2]) == [0.0, 1.0]


def test_source_never_picks_terms_with_an_unstable_sort():
    unstable = re.compile(r"max_features|argpartition|argsort\((?![^)]*kind=\"stable\")")
    found = [
        f"{path.relative_to(PROJECT_ROOT).as_posix()}:{number}"
        for path in sorted((PROJECT_ROOT / "src").rglob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if unstable.search(line)
    ]
    assert not found, (
        f"Unstable term choice is banned in {found}: ties resolve differently per CPU. "
        "Use src.themes.terms.weigh_terms and src.themes.terms.highest_first."
    )
