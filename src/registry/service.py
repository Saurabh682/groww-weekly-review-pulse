from dataclasses import dataclass
from typing import Dict, List, Optional

from src.ingest.sources import ListingNotFound
from src.registry.dispatch import BackfillDispatcher, DispatchResult
from src.registry.resolve import Candidate, ResolveError, Resolver, SearchResult, validate_country
from src.registry.slug import InvalidDisplayName, clean_display_name, unique_app_key
from src.store.errors import ActiveAppCapReached, DuplicateStoreListing, InvalidAppRecord
from src.store.models import AppRecord
from src.store.store import PulseStore

ACTIVE_APP_CAP = 5
LANG_DEFAULT = "en"


class RegistrationRejected(Exception):
    pass


@dataclass
class ListingRequest:
    display_name: str
    play_package_id: Optional[str] = None
    app_store_id: Optional[str] = None
    country: str = "in"
    lang: str = LANG_DEFAULT


BACKFILL_MESSAGES = {
    "dispatched": "Backfill started.",
    "failed": "Backfill is queued for the next daily run.",
    "not_configured": "Backfill is queued for the next daily run.",
}


@dataclass
class Registration:
    app: AppRecord
    slots_used: int
    dispatch: DispatchResult

    def to_dict(self) -> Dict:
        return {
            "app": app_to_dict(self.app),
            "slots_used": self.slots_used,
            "slots_total": ACTIVE_APP_CAP,
            "backfill_dispatch": {
                "status": self.dispatch.status,
                "detail": self.dispatch.detail,
                "message": BACKFILL_MESSAGES[self.dispatch.status],
            },
        }


def app_to_dict(app: AppRecord) -> Dict:
    return {
        "app_key": app.app_key,
        "display_name": app.display_name,
        "status": app.status,
        "play_package_id": app.play_package_id,
        "app_store_id": app.app_store_id,
        "country": app.country,
        "lang": app.lang,
        "category": app.category,
        "created_at": app.created_at,
        "archived_at": app.archived_at,
    }


class RegistryService:
    def __init__(self, store: PulseStore, resolver: Resolver, dispatcher: BackfillDispatcher):
        self.store = store
        self.resolver = resolver
        self.dispatcher = dispatcher

    def search(self, term: str, country: str, lang: str = LANG_DEFAULT) -> SearchResult:
        return self.resolver.search(term, country, lang)

    def list_apps(self, include_archived: bool = False) -> List[AppRecord]:
        apps = self.store.list_apps()
        return apps if include_archived else [a for a in apps if a.status != "archived"]

    def slots_used(self) -> int:
        return self.store.count_live_apps()

    def _verified(self, request: ListingRequest) -> List[Candidate]:
        if not request.play_package_id and not request.app_store_id:
            raise RegistrationRejected("Choose at least one store listing.")
        verified = []
        try:
            if request.play_package_id:
                verified.append(self.resolver.verify_play(request.play_package_id, request.country, request.lang))
            if request.app_store_id:
                verified.append(self.resolver.verify_app_store(request.app_store_id, request.country))
        except (ListingNotFound, ResolveError) as exc:
            raise RegistrationRejected(str(exc)) from exc
        return verified

    def _check_listing_free(self, request: ListingRequest, replacing: Optional[str] = None) -> None:
        for platform, listing_id in (("play_store", request.play_package_id), ("app_store", request.app_store_id)):
            if not listing_id:
                continue
            owner = self.store.live_app_with_listing(platform, listing_id)
            if owner and owner.app_key != replacing:
                raise DuplicateStoreListing(f"{listing_id} already belongs to {owner.display_name} ({owner.app_key}).")

    def _new_record(self, request: ListingRequest, verified: List[Candidate]) -> AppRecord:
        try:
            display_name = clean_display_name(request.display_name)
        except InvalidDisplayName as exc:
            raise InvalidAppRecord(str(exc)) from exc
        category = next((c.category for c in verified if c.platform == "play_store" and c.category), None)
        category = category or next((c.category for c in verified if c.category), None)
        return AppRecord(
            app_key=unique_app_key(display_name, self.store.app_keys()),
            display_name=display_name,
            status="pending_backfill",
            play_package_id=request.play_package_id or None,
            app_store_id=request.app_store_id or None,
            country=validate_country(request.country),
            lang=request.lang,
            category=category,
        )

    def _precheck_cap(self) -> None:
        if self.store.count_live_apps() >= ACTIVE_APP_CAP:
            raise ActiveAppCapReached(f"{ACTIVE_APP_CAP} of {ACTIVE_APP_CAP} active app slots are used. Archive an app first.")

    def register(self, request: ListingRequest) -> Registration:
        self._precheck_cap()
        self._check_listing_free(request)
        record = self._new_record(request, self._verified(request))
        app = self.store.insert_app(record)
        return Registration(app, self.store.count_live_apps(), self.dispatcher.dispatch_backfill(app.app_key))

    def replace(self, old_key: str, request: ListingRequest) -> Registration:
        self.store.get_app(old_key)
        self._check_listing_free(request, replacing=old_key)
        record = self._new_record(request, self._verified(request))
        app = self.store.replace_app(old_key, record)
        return Registration(app, self.store.count_live_apps(), self.dispatcher.dispatch_backfill(app.app_key))

    def rename(self, app_key: str, display_name: str) -> AppRecord:
        try:
            return self.store.rename_app(app_key, clean_display_name(display_name))
        except InvalidDisplayName as exc:
            raise InvalidAppRecord(str(exc)) from exc

    def archive(self, app_key: str) -> AppRecord:
        app = self.store.get_app(app_key)
        return app if app.status == "archived" else self.store.set_app_status(app_key, "archived")
