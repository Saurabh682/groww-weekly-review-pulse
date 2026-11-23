import json
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.auth import OperatorAuth, hs256_decoder, parse_operator_emails
from src.ingest.sources import ListingNotFound
from src.registry.cli import run as registry_cli
from src.registry.dispatch import DispatchResult, GitHubDispatcher
from src.registry.resolve import TERM_MAX_CHARS, Resolver
from src.registry.service import ListingRequest, RegistrationRejected, RegistryService
from src.registry.slug import SLUG_MAX_CHARS, clean_display_name, slugify, unique_app_key
from src.store.errors import ActiveAppCapReached, DuplicateStoreListing, UnknownApp
from src.store.models import AppRecord

SECRET = "test-secret-for-hs256-signing-only-32b"
OPERATOR = "operator@example.com"

ITUNES = {
    "groww": [
        {"trackId": 1404871703, "trackName": "Groww Stocks", "artistName": "Groww", "bundleId": "com.nextbillion.groww",
         "artworkUrl100": "https://example.invalid/i.png", "averageUserRating": 4.5, "userRatingCount": 216833,
         "primaryGenreName": "Finance", "sellerUrl": "https://seller.example.invalid", "description": "long text"},
        {"trackId": 310633997, "trackName": "WhatsApp", "artistName": "WhatsApp Inc.", "bundleId": "net.whatsapp.WhatsApp",
         "primaryGenreName": "Social Networking"},
    ],
    "zomato": [{"trackId": 434613896, "trackName": "Zomato", "bundleId": "com.application.zomato", "primaryGenreName": "Food & Drink"}],
}
PLAY_SEARCH = {
    "groww": [{"appId": None, "title": "Groww Stocks"}, {"appId": "in.groww.dash", "title": "Groww Credit", "genre": "Finance"}],
    "zomato": [{"appId": "com.application.zomato", "title": "Zomato", "genre": "Food & Drink"}],
}
PLAY_APPS = {
    "com.nextbillion.groww": {"appId": "com.nextbillion.groww", "title": "Groww Stocks", "genre": "Finance",
                              "ratings": 2574574, "developerEmail": "dev@example.invalid", "developerWebsite": "https://x.invalid"},
    "in.groww.dash": {"appId": "in.groww.dash", "title": "Groww Credit", "genre": "Finance"},
    "com.application.zomato": {"appId": "com.application.zomato", "title": "Zomato", "genre": "Food & Drink"},
    "in.swiggy.android": {"appId": "in.swiggy.android", "title": "Swiggy", "genre": "Food & Drink"},
    "com.five.a": {"appId": "com.five.a", "title": "A", "genre": "Tools"},
    "com.five.b": {"appId": "com.five.b", "title": "B", "genre": "Tools"},
    "com.five.c": {"appId": "com.five.c", "title": "C", "genre": "Tools"},
    "com.five.d": {"appId": "com.five.d", "title": "D", "genre": "Tools"},
    "com.five.e": {"appId": "com.five.e", "title": "E", "genre": "Tools"},
}
IOS_APPS = {"1404871703": ITUNES["groww"][0], "434613896": ITUNES["zomato"][0], "989540920": {"trackId": 989540920, "trackName": "Swiggy", "primaryGenreName": "Food & Drink"}}


class FakeStores:
    def __init__(self, fail_ios=False, fail_play=False, slow_play=0.0):
        self.urls = []
        self.fail_ios = fail_ios
        self.fail_play = fail_play
        self.slow_play = slow_play

    def http_get(self, url):
        self.urls.append(url)
        if self.fail_ios:
            return 503, b""
        query = parse_qs(urlparse(url).query)
        if "/lookup" in url:
            hit = IOS_APPS.get(query["id"][0])
            return 200, json.dumps({"results": [hit] if hit else []}).encode()
        return 200, json.dumps({"results": ITUNES.get(query["term"][0].lower(), [])}).encode()

    def play_search(self, term, country, lang):
        if self.slow_play:
            time.sleep(self.slow_play)
        if self.fail_play:
            raise RuntimeError("upstream exploded with internal detail")
        return PLAY_SEARCH.get(term.lower(), [])

    def play_lookup(self, package_id, country, lang):
        if package_id not in PLAY_APPS:
            raise ListingNotFound(f"Play Store listing not found: {package_id}")
        return PLAY_APPS[package_id]


class FakeDispatcher:
    def __init__(self, status="dispatched"):
        self.calls = []
        self.status = status

    def dispatch_backfill(self, app_key):
        self.calls.append(app_key)
        return DispatchResult(self.status)


def _resolver(stores=None, timeout_s=5.0):
    stores = stores or FakeStores()
    return Resolver(http_get=stores.http_get, play_search=stores.play_search, play_lookup=stores.play_lookup,
                    timeout_s=timeout_s)


@pytest.fixture
def dispatcher():
    return FakeDispatcher()


@pytest.fixture
def service(pulse_store, dispatcher):
    return RegistryService(pulse_store, _resolver(), dispatcher)


def _token(email=OPERATOR, secret=SECRET, exp_offset=3600):
    return jwt.encode({"sub": "user-1", "email": email, "aud": "authenticated", "exp": int(time.time()) + exp_offset},
                      secret, algorithm="HS256")


@pytest.fixture
def client(service, tmp_path):
    auth = OperatorAuth(hs256_decoder(SECRET), parse_operator_emails(f" {OPERATOR.upper()} , other@example.com"))
    return TestClient(create_app(service, auth, tmp_path, []))


def _auth(email=OPERATOR):
    return {"Authorization": f"Bearer {_token(email)}"}


def _fill_to_five(service):
    for name in ("a", "b", "c", "d"):
        service.register(ListingRequest(f"App {name.upper()}", play_package_id=f"com.five.{name}"))


def test_RES_01_top3_no_autoregister(service):
    result = service.search("groww", "in")
    ios = result.stores["app_store"]
    assert [c.listing_id for c in ios.candidates] == ["1404871703", "310633997"]
    play = result.stores["play_store"]
    assert play.candidates[0].listing_id == "com.nextbillion.groww"
    assert play.candidates[0].matched_by == "app_store_bundle_id"
    assert len(play.candidates) <= 3
    assert len(service.list_apps()) == 1


def test_RES_02_one_store_empty(pulse_store):
    stores = FakeStores()
    PLAY_SEARCH["onlyios"] = []
    ITUNES["onlyios"] = [{"trackId": 1, "trackName": "Only iOS", "bundleId": "com.no.such.play"}]
    result = _resolver(stores).search("onlyios", "in")
    assert result.stores["play_store"].status == "empty"
    assert result.stores["play_store"].message == "Not found on this store."
    assert result.stores["app_store"].status == "ok"


def test_RES_03_no_matches():
    result = _resolver().search("nothing-matches-this", "in")
    assert result.no_matches is True


def test_RES_04_store_failure_isolated():
    result = _resolver(FakeStores(fail_play=True)).search("zomato", "in")
    assert result.stores["play_store"].status == "error"
    assert "exploded" not in json.dumps(result.to_dict())
    assert result.stores["app_store"].candidates[0].listing_id == "434613896"


def test_RES_04_store_timeout_isolated():
    started = time.time()
    result = _resolver(FakeStores(slow_play=3.0), timeout_s=0.5).search("zomato", "in")
    assert time.time() - started < 2.5
    assert result.stores["play_store"].status == "error"
    assert result.stores["app_store"].status == "ok"


def test_play_top_match_without_id_is_flagged():
    PLAY_SEARCH["mystery"] = [{"appId": None, "title": "Mystery"}]
    result = _resolver().search("mystery", "in")
    assert "package name" in result.stores["play_store"].message


def test_RES_05_verify_missing_listing(service):
    with pytest.raises(RegistrationRejected, match="listing not found"):
        service.register(ListingRequest("Ghost", play_package_id="com.does.not.exist"))
    with pytest.raises(RegistrationRejected, match="listing not found"):
        service.register(ListingRequest("Ghost", app_store_id="999"))
    assert len(service.list_apps()) == 1


def test_RES_06_verify_any_id(service, dispatcher):
    reg = service.register(ListingRequest("Swiggy", play_package_id="in.swiggy.android", app_store_id="989540920"))
    assert reg.app.app_key == "swiggy"
    assert reg.app.status == "pending_backfill"
    assert reg.app.category == "Food & Drink"
    assert dispatcher.calls == ["swiggy"]


def test_RES_07_search_term_sanitized():
    stores = FakeStores()
    _resolver(stores).search("  groww&entity=x\x00\n" + "y" * 600, "in")
    query = parse_qs(urlparse(stores.urls[0]).query)
    assert query["entity"] == ["software"]
    assert len(query["term"][0]) == TERM_MAX_CHARS
    assert "\x00" not in query["term"][0]


def test_RES_08_country_validated():
    with pytest.raises(Exception, match="two-letter"):
        _resolver().search("groww", "india")


def test_RES_09_search_field_allowlist(service):
    blob = json.dumps(service.search("groww", "in").to_dict())
    for leaked in ("sellerUrl", "seller.example.invalid", "long text", "developerEmail", "dev@example.invalid"):
        assert leaked not in blob


def test_APP_01_sixth_app_rejected(service, dispatcher):
    _fill_to_five(service)
    assert service.slots_used() == 5
    with pytest.raises(ActiveAppCapReached, match="5 of 5"):
        service.register(ListingRequest("App E", play_package_id="com.five.e"))
    assert "app-e" not in dispatcher.calls


def test_APP_02_concurrent_add_cap(service):
    for name in ("a", "b", "c"):
        service.register(ListingRequest(f"App {name}", play_package_id=f"com.five.{name}"))
    outcomes = []

    def add(name):
        try:
            service.store.insert_app(AppRecord(f"race-{name}", name, "pending_backfill", play_package_id=f"com.five.{name}"))
            outcomes.append("ok")
        except ActiveAppCapReached:
            outcomes.append("cap")

    threads = [threading.Thread(target=add, args=(n,)) for n in ("d", "e")]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(outcomes) == ["cap", "ok"]


def test_APP_03_duplicate_play_listing(service):
    with pytest.raises(DuplicateStoreListing, match="Groww"):
        service.register(ListingRequest("Groww Again", play_package_id="com.nextbillion.groww"))


def test_APP_04_duplicate_ios_listing(service):
    with pytest.raises(DuplicateStoreListing, match="Groww"):
        service.register(ListingRequest("Groww iOS", app_store_id="1404871703"))


def test_APP_07_rename_keeps_history(service):
    groww = service.store.for_app("groww")
    groww.record_run_start("run-1", "2026-11-16")
    renamed = service.rename("groww", "  Groww   Invest ")
    assert renamed.display_name == "Groww Invest"
    assert renamed.play_package_id == "com.nextbillion.groww"
    assert service.store.for_app("groww").get_run("run-1") is not None


def test_APP_08_replace_atomic(service):
    reg = service.replace("groww", ListingRequest("Groww", play_package_id="com.nextbillion.groww", app_store_id="1404871703"))
    assert reg.app.app_key == "groww-2"
    assert service.store.get_app("groww").status == "archived"
    _fill_to_five(service)
    swapped = service.replace("app-a", ListingRequest("App E", play_package_id="com.five.e"))
    assert swapped.app.app_key == "app-e"
    assert service.slots_used() == 5


def test_APP_08_replace_failure_leaves_old_app(service):
    service.register(ListingRequest("Zomato", play_package_id="com.application.zomato"))
    with pytest.raises(DuplicateStoreListing):
        service.store.replace_app("groww", AppRecord("groww-x", "G", "pending_backfill", play_package_id="com.application.zomato"))
    assert service.store.get_app("groww").status == "active"


def test_APP_09_archive_frees_slot(service):
    _fill_to_five(service)
    service.archive("app-a")
    assert service.slots_used() == 4
    assert service.store.for_app("app-a").app.archived_at is not None
    service.register(ListingRequest("App E", play_package_id="com.five.e"))


def test_APP_10_readd_archived_listing(service):
    service.archive("groww")
    reg = service.register(ListingRequest("Groww", play_package_id="com.nextbillion.groww"))
    assert reg.app.app_key == "groww-2"
    assert service.store.get_app("groww").status == "archived"


def test_APP_11_app_key_collision():
    assert unique_app_key("Groww", ["groww"]) == "groww-2"
    assert unique_app_key("Groww", ["groww", "groww-2"]) == "groww-3"


def test_APP_12_display_name_bounds():
    assert slugify("Zomato 🍕 Food") == "zomato-food"
    assert slugify("ग्रो") == "app"
    long_slug = slugify("x" * 200)
    assert 0 < len(long_slug) <= SLUG_MAX_CHARS
    assert len(unique_app_key("x" * 200, [long_slug])) <= SLUG_MAX_CHARS
    assert len(clean_display_name("y" * 200)) == 80


def test_AUTH_01_no_token(client):
    assert client.post("/search", json={"name": "groww"}).status_code == 401


def test_AUTH_02_not_operator(client):
    response = client.post("/search", json={"name": "groww"}, headers=_auth("stranger@example.com"))
    assert response.status_code == 403


def test_AUTH_03_bad_token(client):
    expired = {"Authorization": f"Bearer {_token(exp_offset=-10)}"}
    tampered = {"Authorization": f"Bearer {_token(secret='another-secret-that-is-long-enough-x')}"}
    assert client.post("/search", json={"name": "groww"}, headers=expired).status_code == 401
    assert client.post("/search", json={"name": "groww"}, headers=tampered).status_code == 401


def test_auth_not_configured_refuses_writes(service, tmp_path):
    unconfigured = TestClient(create_app(service, OperatorAuth(None, frozenset()), tmp_path, []))
    assert unconfigured.delete("/apps/groww", headers=_auth()).status_code == 503
    assert service.store.get_app("groww").status == "active"


def test_AUTH_04_public_reads_safe(client, service, tmp_path):
    groww = service.store.for_app("groww")
    from src.store.models import ReviewRecord
    groww.upsert_reviews([ReviewRecord("r1", "play_store", 2, "SECRET RAW REVIEW TEXT", "2026-11-20", raw_hash="h")])
    for path in ("/apps", "/apps/groww/pulses", "/apps/groww/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert "SECRET RAW REVIEW TEXT" not in response.text


ROUTE_AUTH = {
    ("GET", "/apps"): False,
    ("POST", "/search"): True,
    ("POST", "/apps"): True,
    ("PATCH", "/apps/{app_key}"): True,
    ("POST", "/apps/{app_key}/replace"): True,
    ("DELETE", "/apps/{app_key}"): True,
    ("GET", "/apps/{app_key}/pulses"): False,
    ("GET", "/apps/{app_key}/pulses/{week}"): False,
    ("GET", "/apps/{app_key}/health"): False,
}
DOC_ROUTES = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}
SAMPLE_BODY = {"display_name": "X", "play_package_id": "com.five.a"}


def test_AUTH_05_route_auth_table(client):
    routes = {(m, r.path) for r in client.app.routes if r.path not in DOC_ROUTES for m in r.methods - {"HEAD"}}
    assert routes == set(ROUTE_AUTH)
    for (method, path), needs_auth in ROUTE_AUTH.items():
        url = path.replace("{app_key}", "groww").replace("{week}", "2026-11-16")
        body = SAMPLE_BODY if method in ("POST", "PATCH") else None
        if path == "/search":
            body = {"name": "groww"}
        if path == "/apps/{app_key}" and method == "PATCH":
            body = {"display_name": "X"}
        status = client.request(method, url, json=body).status_code
        assert (status == 401) == needs_auth, (method, path, status)


def test_api_register_and_errors(client, dispatcher):
    created = client.post("/apps", headers=_auth(), json={"display_name": "Zomato", "play_package_id": "com.application.zomato"})
    assert created.status_code == 201
    assert created.json()["slots_used"] == 2
    assert created.json()["backfill_dispatch"]["status"] == "dispatched"
    dup = client.post("/apps", headers=_auth(), json={"display_name": "Z2", "play_package_id": "com.application.zomato"})
    assert dup.status_code == 409
    missing = client.post("/apps", headers=_auth(), json={"display_name": "Ghost", "play_package_id": "com.no.such"})
    assert missing.status_code == 422
    assert client.patch("/apps/nope", headers=_auth(), json={"display_name": "X"}).status_code == 404


def test_api_rename_accepts_only_display_name(client):
    response = client.patch("/apps/groww", headers=_auth(), json={"display_name": "G", "play_package_id": "com.other"})
    assert response.status_code == 422


def test_api_sixth_app_409(client, service):
    _fill_to_five(service)
    response = client.post("/apps", headers=_auth(), json={"display_name": "E", "play_package_id": "com.five.e"})
    assert response.status_code == 409
    assert "5 of 5" in response.json()["error"]


def test_dispatch_failure_leaves_pending(pulse_store):
    service = RegistryService(pulse_store, _resolver(), FakeDispatcher(status="failed"))
    reg = service.register(ListingRequest("Zomato", play_package_id="com.application.zomato"))
    assert reg.dispatch.status == "failed"
    assert service.store.get_app("zomato").status == "pending_backfill"


def test_github_dispatcher_request():
    sent = {}

    def post(url, body, headers):
        sent.update(url=url, body=json.loads(body), headers=headers)
        return 204, b""

    result = GitHubDispatcher("owner/repo", "tok", http_post=post).dispatch_backfill("zomato")
    assert result.status == "dispatched"
    assert sent["url"] == "https://api.github.com/repos/owner/repo/actions/workflows/pulse.yml/dispatches"
    assert sent["body"] == {"ref": "main", "inputs": {"mode": "backfill", "app_key": "zomato"}}
    assert sent["headers"]["Authorization"] == "Bearer tok"
    assert GitHubDispatcher("o/r", "t", http_post=lambda u, b, h: (404, b"")).dispatch_backfill("x").status == "failed"


def test_registry_cli(service, capsys):
    assert registry_cli(["list", "--keys"], service=service) == 0
    assert json.loads(capsys.readouterr().out) == ["groww"]
    assert registry_cli(["add", "--name", "Zomato", "--play", "com.application.zomato"], service=service) == 0
    assert json.loads(capsys.readouterr().out)["app"]["app_key"] == "zomato"
    assert registry_cli(["archive", "--app", "nope"], service=service) == 2
    assert "error" in capsys.readouterr().err
    with pytest.raises(UnknownApp):
        service.store.get_app("nope")
