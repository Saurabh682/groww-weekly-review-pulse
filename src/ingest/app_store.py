import json
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional, Tuple

from src.clean.normalize import normalize_text, validate_and_coerce_rating
from src.ingest.sources import (
    ListingNotFound,
    RetryableStatus,
    SourceError,
    SourceResult,
    call_with_retries,
    finish_window,
)

PLATFORM = "app_store"
MAX_PAGES = 10
PAGE_DELAY_S = 1.0
FEED_URL = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/{fmt}"
FEED_FORMATS = ("json", "xml")
ATOM = "{http://www.w3.org/2005/Atom}"
ITUNES = "{http://itunes.apple.com/rss}"
USER_AGENT = "weekly-review-pulse/0.1"
RETRYABLE_STATUSES = (429, 500, 502, 503, 504)
RETRYABLE_ERRORS = (RetryableStatus, urllib.error.URLError, TimeoutError, ConnectionError)

HttpGet = Callable[[str], Tuple[int, bytes]]


def urllib_get(url: str) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


def _label(entry: dict, key: str) -> str:
    value = entry.get(key)
    return str(value.get("label", "")) if isinstance(value, dict) else ""


def _entry_date(entry: dict) -> str:
    raw = _label(entry, "updated")
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise SourceError(f"App Store review has an unexpected date value: {raw!r}") from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).date().isoformat()


def map_app_store_entry(entry: Any) -> Optional[dict]:
    if not isinstance(entry, dict) or "im:rating" not in entry:
        return None
    text = normalize_text(_label(entry, "content"))
    if not text:
        return None
    return {
        "platform": PLATFORM,
        "rating": validate_and_coerce_rating(_label(entry, "im:rating")),
        "title": normalize_text(_label(entry, "title")) or None,
        "text": text,
        "date": _entry_date(entry),
        "app_version": normalize_text(_label(entry, "im:version")) or None,
    }


def parse_feed_page(body: bytes) -> List[Any]:
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceError("App Store feed returned a body that is not JSON.") from exc
    feed = data.get("feed") if isinstance(data, dict) else None
    if not isinstance(feed, dict):
        raise SourceError("App Store feed has no 'feed' object.")
    entries = feed.get("entry", [])
    return [entries] if isinstance(entries, dict) else list(entries)


def _xml_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return (child.text or "") if child is not None else ""


def _xml_entry(element: ET.Element) -> dict:
    content = next((c.text or "" for c in element.findall(f"{ATOM}content") if c.get("type") == "text"), "")
    entry = {
        "title": {"label": _xml_text(element, f"{ATOM}title")},
        "content": {"label": content},
        "updated": {"label": _xml_text(element, f"{ATOM}updated")},
        "im:version": {"label": _xml_text(element, f"{ITUNES}version")},
    }
    if element.find(f"{ITUNES}rating") is not None:
        entry["im:rating"] = {"label": _xml_text(element, f"{ITUNES}rating")}
    return entry


def parse_feed_xml(body: bytes) -> List[Any]:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise SourceError("App Store feed returned a body that is not XML.") from exc
    return [_xml_entry(e) for e in root.findall(f"{ATOM}entry")]


PARSERS = {"json": parse_feed_page, "xml": parse_feed_xml}


class AppStoreSource:
    platform = PLATFORM

    def __init__(
        self,
        app_store_id: str,
        country: str,
        http_get: HttpGet = urllib_get,
        sleep: Callable[[float], None] = time.sleep,
        max_pages: int = MAX_PAGES,
    ):
        self.app_store_id = app_store_id
        self.country = country
        self._http_get = http_get
        self._sleep = sleep
        self._max_pages = max_pages

    def _get_format(self, page: int, fmt: str) -> List[Any]:
        url = FEED_URL.format(country=self.country, page=page, app_id=self.app_store_id, fmt=fmt)

        def attempt() -> Tuple[int, bytes]:
            status, body = self._http_get(url)
            if status in RETRYABLE_STATUSES:
                raise RetryableStatus(f"HTTP {status}")
            return status, body

        status, body = call_with_retries(attempt, RETRYABLE_ERRORS, self._sleep)
        if status == 404 and page == 1:
            raise ListingNotFound(f"App Store listing not found: {self.app_store_id}")
        if status != 200:
            raise SourceError(f"App Store feed returned HTTP {status} on page {page}.")
        return PARSERS[fmt](body)

    def _get_reviews(self, page: int) -> List[dict]:
        for fmt in FEED_FORMATS:
            entries = self._get_format(page, fmt)
            reviews = [m for m in (map_app_store_entry(e) for e in entries) if m is not None]
            if reviews:
                return reviews
        return []

    def fetch(self, window_start: str, window_end: str) -> SourceResult:
        result = SourceResult()
        reached_start = False
        while result.pages < self._max_pages and not reached_start:
            if result.pages:
                self._sleep(PAGE_DELAY_S)
            reviews = self._get_reviews(result.pages + 1)
            result.pages += 1
            if not reviews:
                result.feed_gaps += 1
                continue
            result.fetched += len(reviews)
            for mapped in reviews:
                if mapped["date"] < window_start:
                    reached_start = True
                    break
                if mapped["date"] <= window_end:
                    result.records.append(mapped)
        return finish_window(result, reached_start, window_start)
