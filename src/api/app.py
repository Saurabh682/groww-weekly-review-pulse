from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.api.auth import AuthError, OperatorAuth
from src.ingest.sources import ListingNotFound
from src.registry.resolve import ResolveError
from src.registry.service import ACTIVE_APP_CAP, ListingRequest, RegistrationRejected, RegistryService, app_to_dict
from src.store.errors import (
    ActiveAppCapReached,
    AppIdentityFrozen,
    DuplicateStoreListing,
    InvalidAppRecord,
    StoreError,
    UnknownApp,
)
from src.store.models import PLATFORMS

PULSE_LIMIT_MAX = 52
ERROR_STATUS = (
    (AuthError, None),
    (UnknownApp, 404),
    (ActiveAppCapReached, 409),
    (DuplicateStoreListing, 409),
    (AppIdentityFrozen, 409),
    (InvalidAppRecord, 422),
    (RegistrationRejected, 422),
    (ListingNotFound, 422),
    (ResolveError, 422),
    (StoreError, 500),
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchBody(StrictModel):
    name: str = Field(min_length=1, max_length=500)
    country: str = "in"


class ListingBody(StrictModel):
    display_name: str = Field(min_length=1, max_length=500)
    play_package_id: Optional[str] = Field(default=None, max_length=200)
    app_store_id: Optional[str] = Field(default=None, max_length=20)
    country: str = "in"
    lang: str = "en"

    def to_request(self) -> ListingRequest:
        return ListingRequest(self.display_name, self.play_package_id, self.app_store_id, self.country, self.lang)


class RenameBody(StrictModel):
    display_name: str = Field(min_length=1, max_length=500)


def _theme_dict(theme) -> Dict:
    return {
        "label": theme.label,
        "review_count": theme.review_count,
        "share_pct": theme.share_pct,
        "avg_rating": theme.avg_rating,
        "is_top3": bool(theme.is_top3),
    }


def _collection_dict(run) -> Optional[Dict]:
    if run is None:
        return None
    return {
        "platform": run.platform,
        "mode": run.mode,
        "status": run.status,
        "window_start": run.window_start,
        "window_end": run.window_end,
        "covered_start": run.covered_start,
        "fetched": run.fetched,
        "inserted": run.inserted,
        "source_limit_hit": bool(run.source_limit_hit),
        "feed_gaps": run.feed_gaps,
        "error": run.error,
        "finished_at": run.finished_at,
    }


def create_app(service: RegistryService, auth: OperatorAuth, outputs_root: Path, cors_origins: List[str]) -> FastAPI:
    api = FastAPI(title="Weekly Review Pulse API", version="2.0.0")
    if cors_origins:
        api.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_methods=["*"],
                           allow_headers=["Authorization", "Content-Type"])

    for exc_type, status in ERROR_STATUS:
        def handler(request: Request, exc: Exception, status: Optional[int] = status) -> JSONResponse:
            code = getattr(exc, "status_code", None) if status is None else status
            return JSONResponse(status_code=code or 500, content={"error": str(exc)})

        api.add_exception_handler(exc_type, handler)

    def operator(authorization: Optional[str] = Header(default=None)) -> str:
        return auth.operator_email(authorization)

    def app_store(app_key: str):
        return service.store.for_app(app_key)

    @api.get("/apps")
    def list_apps(include_archived: bool = False) -> Dict:
        apps = service.list_apps(include_archived=include_archived)
        return {"slots_used": service.slots_used(), "slots_total": ACTIVE_APP_CAP, "apps": [app_to_dict(a) for a in apps]}

    @api.post("/search")
    def search(body: SearchBody, _: str = Depends(operator)) -> Dict:
        return service.search(body.name, body.country).to_dict()

    @api.post("/apps", status_code=201)
    def register(body: ListingBody, _: str = Depends(operator)) -> Dict:
        return service.register(body.to_request()).to_dict()

    @api.patch("/apps/{app_key}")
    def rename(app_key: str, body: RenameBody, _: str = Depends(operator)) -> Dict:
        return app_to_dict(service.rename(app_key, body.display_name))

    @api.post("/apps/{app_key}/replace", status_code=201)
    def replace(app_key: str, body: ListingBody, _: str = Depends(operator)) -> Dict:
        return service.replace(app_key, body.to_request()).to_dict()

    @api.delete("/apps/{app_key}")
    def archive(app_key: str, _: str = Depends(operator)) -> Dict:
        return app_to_dict(service.archive(app_key))

    @api.get("/apps/{app_key}/pulses")
    def pulses(app_key: str, limit: int = Query(default=12, ge=1, le=PULSE_LIMIT_MAX)) -> Dict:
        store = app_store(app_key)
        weeks = []
        for row in store.list_pulse_weeks(limit):
            themes = [t for t in store.get_themes(row["run_id"]) if t.is_top3]
            weeks.append({
                "week_start": row["week_start"],
                "status": row["status"],
                "total_reviews": row["total_reviews"],
                "analyzed_reviews": row["analyzed_reviews"],
                "avg_rating": row["avg_rating"],
                "doc_url": row["doc_url"],
                "draft_created": bool(row["draft_id"]),
                "published_at": row["published_at"],
                "top_themes": [_theme_dict(t) for t in themes],
            })
        return {"app_key": app_key, "pulses": weeks}

    @api.get("/apps/{app_key}/pulses/{week}")
    def pulse(app_key: str, week: str) -> Dict:
        store = app_store(app_key)
        run = store.latest_themed_run_for_week(week)
        if run is None:
            raise UnknownApp(f"No pulse for {app_key} in week {week}.")
        note_path = outputs_root / app_key / week / "note.md"
        state = store.get_publish_state(week)
        return {
            "app_key": app_key,
            "week_start": week,
            "status": run.status,
            "window_start": run.window_start,
            "window_end": run.window_end,
            "themes": [_theme_dict(t) for t in store.get_themes(run.run_id)],
            "note_markdown": note_path.read_text(encoding="utf-8") if note_path.is_file() else None,
            "doc_url": state.doc_url if state else None,
            "draft_created": bool(state and state.draft_id),
        }

    @api.get("/apps/{app_key}/health")
    def health(app_key: str) -> Dict:
        store = app_store(app_key)
        return {
            "app": app_to_dict(store.app),
            "collections": {p: _collection_dict(store.latest_finished_collection(p)) for p in PLATFORMS},
            "latest_pulse": next(iter(store.list_pulse_weeks(1)), None),
        }

    return api
