import time
import urllib.error
from datetime import date, datetime, timezone
from typing import Any, Callable, List, Optional, Tuple

from src.clean.normalize import normalize_text, validate_and_coerce_rating
from src.ingest.sources import (
    ListingNotFound,
    SourceError,
    SourceResult,
    call_with_retries,
    finish_window,
)

PLATFORM = "play_store"
PAGE_SIZE = 200
PAGE_DELAY_S = 1.0
MAX_PAGES = 100

PageFetcher = Callable[[Optional[Any]], Tuple[List[dict], Optional[Any]]]
ListingCheck = Callable[[], None]


def _review_date(raw: Any) -> str:
    if isinstance(raw, datetime):
        moment = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    raise SourceError(f"Play Store review has an unexpected date value: {type(raw).__name__}")


def map_play_item(item: Any) -> Optional[dict]:
    if not isinstance(item, dict) or "score" not in item or "at" not in item:
        raise SourceError("Play Store returned a review without score or date.")
    text = normalize_text(item.get("content") or "")
    if not text:
        return None
    return {
        "platform": PLATFORM,
        "rating": validate_and_coerce_rating(item["score"]),
        "title": None,
        "text": text,
        "date": _review_date(item["at"]),
        "app_version": normalize_text(item.get("reviewCreatedVersion") or "") or None,
    }


def _default_fetcher(package_id: str, country: str, lang: str) -> PageFetcher:
    from google_play_scraper import Sort, reviews

    def fetch(token: Optional[Any]) -> Tuple[List[dict], Optional[Any]]:
        return reviews(package_id, lang=lang, country=country, sort=Sort.NEWEST,
                       count=PAGE_SIZE, continuation_token=token)

    return fetch


def _default_listing_check(package_id: str, country: str, lang: str) -> ListingCheck:
    from google_play_scraper import app
    from google_play_scraper.exceptions import NotFoundError

    def check() -> None:
        try:
            app(package_id, lang=lang, country=country)
        except NotFoundError as exc:
            raise ListingNotFound(f"Play Store listing not found: {package_id}") from exc

    return check


def retryable_play_errors() -> tuple:
    from google_play_scraper.exceptions import ExtraHTTPError

    return (ExtraHTTPError, urllib.error.URLError, TimeoutError, ConnectionError)


class PlayStoreSource:
    platform = PLATFORM

    def __init__(
        self,
        package_id: str,
        country: str,
        lang: str,
        fetch_page: Optional[PageFetcher] = None,
        check_listing: Optional[ListingCheck] = None,
        sleep: Callable[[float], None] = time.sleep,
        max_pages: int = MAX_PAGES,
    ):
        self.package_id = package_id
        self._fetch_page = fetch_page or _default_fetcher(package_id, country, lang)
        self._check_listing = check_listing or _default_listing_check(package_id, country, lang)
        self._sleep = sleep
        self._max_pages = max_pages

    def fetch(self, window_start: str, window_end: str) -> SourceResult:
        result = SourceResult()
        token: Optional[Any] = None
        reached_start = False
        while result.pages < self._max_pages and not reached_start:
            if result.pages:
                self._sleep(PAGE_DELAY_S)
            current = token
            batch, token = call_with_retries(
                lambda: self._fetch_page(current), retryable_play_errors(), self._sleep
            )
            result.pages += 1
            if not isinstance(batch, list):
                raise SourceError("Play Store returned an unexpected page shape.")
            if result.pages == 1 and not batch:
                self._check_listing()
            result.fetched += len(batch)
            for item in batch:
                mapped = map_play_item(item)
                if mapped is None:
                    continue
                if mapped["date"] < window_start:
                    reached_start = True
                    break
                if mapped["date"] <= window_end:
                    result.records.append(mapped)
            if not batch or token is None:
                reached_start = True
        return finish_window(result, reached_start, window_start)
