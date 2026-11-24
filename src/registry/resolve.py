import json
import re
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.ingest.app_store import urllib_get
from src.ingest.sources import ListingNotFound

TOP_N = 3
TERM_MAX_CHARS = 100
STORE_TIMEOUT_S = 10.0
ITUNES_SEARCH_URL = "https://itunes.apple.com/search?{query}"
ITUNES_LOOKUP_URL = "https://itunes.apple.com/lookup?{query}"
PLAY_UNIDENTIFIED_MESSAGE = (
    "The top Play Store match could not be identified. If your app is missing, paste its package name "
    "from the Play Store URL (the id= part)."
)
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
PLAY_PACKAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")
APP_STORE_ID = re.compile(r"^[0-9]{1,12}$")
COUNTRY = re.compile(r"^[a-z]{2}$")

HttpGet = Callable[[str], Tuple[int, bytes]]
PlaySearch = Callable[[str, str, str], List[dict]]
PlayLookup = Callable[[str, str, str], dict]


class ResolveError(Exception):
    pass


@dataclass
class Candidate:
    platform: str
    listing_id: str
    title: str
    developer: Optional[str] = None
    icon_url: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    category: Optional[str] = None
    matched_by: str = "search"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StoreSearch:
    platform: str
    status: str
    candidates: List[Candidate] = field(default_factory=list)
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "status": self.status,
            "candidates": [c.to_dict() for c in self.candidates],
            "message": self.message,
        }


@dataclass
class SearchResult:
    term: str
    country: str
    stores: Dict[str, StoreSearch]

    @property
    def no_matches(self) -> bool:
        return all(not s.candidates for s in self.stores.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "country": self.country,
            "no_matches": self.no_matches,
            "stores": {k: v.to_dict() for k, v in self.stores.items()},
        }


def sanitize_term(term: str) -> str:
    cleaned = " ".join(CONTROL_CHARS.sub(" ", term or "").split())[:TERM_MAX_CHARS].strip()
    if not cleaned:
        raise ResolveError("Search term is empty.")
    return cleaned


def validate_country(country: str) -> str:
    value = (country or "").strip().lower()
    if not COUNTRY.match(value):
        raise ResolveError("Country must be a two-letter store country code, e.g. 'in'.")
    return value


def validate_play_package(package_id: str) -> str:
    if not PLAY_PACKAGE.match(package_id or ""):
        raise ResolveError(f"Not a valid Play package name: {package_id!r}")
    return package_id


def validate_app_store_id(app_store_id: str) -> str:
    if not APP_STORE_ID.match(app_store_id or ""):
        raise ResolveError(f"Not a valid App Store ID: {app_store_id!r}")
    return app_store_id


def _itunes_candidate(item: dict) -> Optional[Candidate]:
    if not isinstance(item, dict) or "trackId" not in item:
        return None
    return Candidate(
        platform="app_store",
        listing_id=str(item["trackId"]),
        title=str(item.get("trackName") or ""),
        developer=item.get("artistName"),
        icon_url=item.get("artworkUrl100"),
        rating=item.get("averageUserRating"),
        rating_count=item.get("userRatingCount"),
        category=item.get("primaryGenreName"),
    )


def _play_candidate(item: dict, matched_by: str = "search") -> Optional[Candidate]:
    if not isinstance(item, dict) or not item.get("appId"):
        return None
    return Candidate(
        platform="play_store",
        listing_id=str(item["appId"]),
        title=str(item.get("title") or ""),
        developer=item.get("developer"),
        icon_url=item.get("icon"),
        rating=item.get("score"),
        rating_count=item.get("ratings"),
        category=item.get("genre"),
        matched_by=matched_by,
    )


def _default_play_search(term: str, country: str, lang: str) -> List[dict]:
    from google_play_scraper import search

    return search(term, n_hits=TOP_N * 2, lang=lang, country=country)


def _default_play_lookup(package_id: str, country: str, lang: str) -> dict:
    from google_play_scraper import app
    from google_play_scraper.exceptions import NotFoundError

    try:
        return app(package_id, lang=lang, country=country)
    except NotFoundError as exc:
        raise ListingNotFound(f"Play Store listing not found: {package_id}") from exc


class Resolver:
    def __init__(
        self,
        http_get: HttpGet = urllib_get,
        play_search: PlaySearch = _default_play_search,
        play_lookup: PlayLookup = _default_play_lookup,
        timeout_s: float = STORE_TIMEOUT_S,
    ):
        self._http_get = http_get
        self._play_search = play_search
        self._play_lookup = play_lookup
        self._timeout_s = timeout_s

    def _itunes(self, url_template: str, params: Dict[str, Any]) -> List[dict]:
        status, body = self._http_get(url_template.format(query=urllib.parse.urlencode(params)))
        if status != 200:
            raise ResolveError(f"App Store returned HTTP {status}.")
        try:
            return json.loads(body.decode("utf-8")).get("results", [])
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
            raise ResolveError("App Store returned an unreadable response.") from exc

    def search_app_store_raw(self, term: str, country: str) -> List[dict]:
        params = {"term": term, "country": country, "entity": "software", "limit": TOP_N}
        return [r for r in self._itunes(ITUNES_SEARCH_URL, params) if isinstance(r, dict)][:TOP_N]

    def search_play(self, term: str, country: str, lang: str) -> Tuple[List[Candidate], int]:
        raw = [r for r in self._play_search(term, country, lang) if isinstance(r, dict)]
        found = [c for c in (_play_candidate(r) for r in raw) if c is not None]
        return found[:TOP_N], len(raw) - len(found)

    def _play_from_bundles(self, bundle_ids: List[str], known: List[str], country: str, lang: str) -> List[Candidate]:
        matches = []
        for bundle_id in bundle_ids:
            if bundle_id in known:
                continue
            try:
                details = self._play_lookup(bundle_id, country, lang)
            except Exception:
                continue
            candidate = _play_candidate(details, matched_by="app_store_bundle_id")
            if candidate:
                matches.append(candidate)
        return matches

    def search(self, term: str, country: str, lang: str = "en") -> SearchResult:
        term = sanitize_term(term)
        country = validate_country(country)
        tasks = {
            "play_store": lambda: self.search_play(term, country, lang),
            "app_store": lambda: self.search_app_store_raw(term, country),
        }
        outcomes: Dict[str, Any] = {}
        pool = ThreadPoolExecutor(max_workers=len(tasks))
        try:
            futures = {name: pool.submit(fn) for name, fn in tasks.items()}
            for name, future in futures.items():
                try:
                    outcomes[name] = future.result(timeout=self._timeout_s)
                except FutureTimeout:
                    outcomes[name] = ResolveError("timed out")
                except Exception as exc:
                    outcomes[name] = exc
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        unidentified = 0
        if isinstance(outcomes["play_store"], tuple):
            outcomes["play_store"], unidentified = outcomes["play_store"]
        raw_ios = outcomes["app_store"]
        bundles: List[str] = []
        if isinstance(raw_ios, list):
            bundles = [str(r["bundleId"]) for r in raw_ios if PLAY_PACKAGE.match(str(r.get("bundleId", "")))]
            outcomes["app_store"] = [c for c in (_itunes_candidate(r) for r in raw_ios) if c is not None]
        stores: Dict[str, StoreSearch] = {}
        for platform in ("play_store", "app_store"):
            outcome = outcomes[platform]
            if isinstance(outcome, Exception):
                stores[platform] = StoreSearch(platform, "error", message="Store search failed. Try again.")
            else:
                stores[platform] = StoreSearch(platform, "ok" if outcome else "empty", list(outcome),
                                               None if outcome else "Not found on this store.")
        play = stores["play_store"]
        if play.status != "error" and unidentified:
            play.message = PLAY_UNIDENTIFIED_MESSAGE
        if play.status != "error" and bundles:
            extra = self._play_from_bundles(bundles, [c.listing_id for c in play.candidates], country, lang)
            play.candidates = (extra + play.candidates)[:TOP_N]
            if extra:
                play.status = "ok"
                play.message = None
        return SearchResult(term, country, stores)

    def verify_play(self, package_id: str, country: str, lang: str = "en") -> Candidate:
        validate_play_package(package_id)
        candidate = _play_candidate(self._play_lookup(package_id, country, lang), matched_by="verify")
        if candidate is None or candidate.listing_id != package_id:
            raise ListingNotFound(f"Play Store listing not found: {package_id}")
        return candidate

    def verify_app_store(self, app_store_id: str, country: str) -> Candidate:
        validate_app_store_id(app_store_id)
        results = self._itunes(ITUNES_LOOKUP_URL, {"id": app_store_id, "country": country})
        candidate = next((c for c in (_itunes_candidate(r) for r in results) if c is not None), None)
        if candidate is None or candidate.listing_id != app_store_id:
            raise ListingNotFound(f"App Store listing not found: {app_store_id}")
        candidate.matched_by = "verify"
        return candidate
