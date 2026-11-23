import argparse
import json
from datetime import datetime
from pathlib import Path

from src.clean.pii import scrub_pii
from src.ingest.app_store import FEED_FORMATS, FEED_URL, MAX_PAGES, PARSERS, urllib_get

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "stores"
PLAY_IDENTITY_PLACEHOLDERS = {
    "reviewId": "fixture-review-id",
    "userName": "Fixture Reviewer",
    "userImage": "https://example.invalid/avatar.png",
    "thumbsUpCount": 7,
    "replyContent": "Fixture developer reply",
    "repliedAt": "2026-01-01T00:00:00",
}
APP_STORE_IDENTITY_PLACEHOLDERS = {
    "author": {"name": {"label": "Fixture Reviewer"}, "uri": {"label": "https://example.invalid/reviewer"}},
    "id": {"label": "fixture-review-id"},
    "link": {"attributes": {"href": "https://example.invalid/review"}},
    "im:voteSum": {"label": "7"},
    "im:voteCount": {"label": "9"},
}


def _scrubbed(text: str) -> str:
    return scrub_pii(text or "").cleaned_text


def record_play(package_id: str, country: str, count: int) -> Path:
    from google_play_scraper import Sort, reviews

    batch, _ = reviews(package_id, lang="en", country=country, sort=Sort.NEWEST, count=count)
    items = []
    for item in batch:
        safe = dict(item)
        safe.update(PLAY_IDENTITY_PLACEHOLDERS)
        safe["content"] = _scrubbed(item.get("content"))
        safe["at"] = item["at"].isoformat() if isinstance(item.get("at"), datetime) else item.get("at")
        items.append(safe)
    path = FIXTURE_DIR / "play_store_page.json"
    path.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    return path


def _first_filled_page(app_store_id: str, country: str) -> list:
    for page in range(1, MAX_PAGES + 1):
        for fmt in FEED_FORMATS:
            status, body = urllib_get(FEED_URL.format(country=country, page=page, app_id=app_store_id, fmt=fmt))
            if status != 200:
                raise SystemExit(f"App Store feed returned HTTP {status}")
            entries = [e for e in PARSERS[fmt](body) if "im:rating" in e]
            if entries:
                return entries
    raise SystemExit("App Store feed returned no reviews on any page")


def record_app_store(app_store_id: str, country: str, count: int) -> Path:
    entries = []
    for entry in _first_filled_page(app_store_id, country)[:count]:
        safe = dict(entry)
        if "im:rating" in safe:
            safe.update(APP_STORE_IDENTITY_PLACEHOLDERS)
            safe["content"] = {"label": _scrubbed(entry.get("content", {}).get("label", "")), "attributes": {"type": "text"}}
            safe["title"] = {"label": _scrubbed(entry.get("title", {}).get("label", ""))}
        entries.append(safe)
    path = FIXTURE_DIR / "app_store_page.json"
    path.write_text(json.dumps({"feed": {"entry": entries}}, indent=1, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Record store responses as test fixtures, identity fields replaced")
    parser.add_argument("--play", required=True)
    parser.add_argument("--app-store", required=True)
    parser.add_argument("--country", default="in")
    parser.add_argument("--count", type=int, default=25)
    args = parser.parse_args()
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    print(record_play(args.play, args.country, args.count))
    print(record_app_store(args.app_store, args.country, args.count))


if __name__ == "__main__":
    main()
