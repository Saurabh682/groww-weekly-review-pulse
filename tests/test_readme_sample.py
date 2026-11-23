import csv
import json

from src.clean.pii import scrub_pii
from src.config import PROJECT_ROOT

SAMPLE = PROJECT_ROOT / "docs" / "samples" / "groww-2026-11-16"
README = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_shows_the_sample_note_unchanged():
    note = (SAMPLE / "note.md").read_text(encoding="utf-8")
    assert f"```markdown\n{note.strip()}\n```" in README


def test_readme_report_summary_matches_the_sample_report():
    report = json.loads((SAMPLE / "run_report.json").read_text(encoding="utf-8"))
    summary = json.loads(README.split("run_report.json`)\n```json\n")[1].split("```")[0])
    assert summary == {key: report[key] for key in summary}


def test_sample_has_no_pii_and_no_fixture_reviews():
    with open(PROJECT_ROOT / "tests" / "fixtures" / "reviews_baseline.csv", encoding="utf-8") as f:
        fixture_texts = [row["text"].strip() for row in csv.DictReader(f)]
    for path in SAMPLE.iterdir():
        text = path.read_text(encoding="utf-8")
        assert not scrub_pii(text).pii_found
        assert [t for t in fixture_texts if t in text] == []
