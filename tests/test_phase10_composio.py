import pytest

from src.mcp.capabilities import MCPConfigData, load_mcp_config, refuse_unlisted_tool
from src.mcp.composio import ComposioClient, ComposioSettings, account_endpoint, decode_rpc_body
from src.mcp.errors import (
    MCPAccountNotPinned,
    MCPAuthError,
    MCPConnectionExpired,
    MCPMissingSetting,
    MCPToolRefused,
)
from src.mcp.publisher import PulsePublisher
from src.pipeline import run_full_pipeline
from src.store.models import AppRecord
from tests.conftest import TEST_RECIPIENT
from tests.support.composio_server import DOCS_ACCOUNT, GMAIL_ACCOUNT, fast_config

WEEK = "2026-11-16"
ENV = {
    "COMPOSIO_MCP_URL": "https://backend.composio.dev/v3/mcp/srv?user_id=u",
    "COMPOSIO_API_KEY": "key",
    "COMPOSIO_GOOGLEDOCS_ACCOUNT_ID": "ca_docs",
    "COMPOSIO_GMAIL_ACCOUNT_ID": "ca_gmail",
}


def _raw_config() -> dict:
    return load_mcp_config("config/mcp.yaml").model_dump()


@pytest.mark.parametrize("slug", ["GMAIL_SEND_EMAIL", "GMAIL_SEND_DRAFT", "GMAIL_DELETE_DRAFT",
                                  "GMAIL_MOVE_TO_TRASH", "GOOGLEDOCS_DELETE_DOCUMENT", "GMAIL_FETCH_EMAILS"])
def test_CMP_01_tool_allowlist(slug):
    with pytest.raises(MCPToolRefused):
        refuse_unlisted_tool(load_mcp_config("config/mcp.yaml"), slug)


def test_CMP_01_send_tool_cannot_enter_the_map():
    raw = _raw_config()
    raw["capabilities"]["gmail.create_draft"]["tool"] = "GMAIL_SEND_EMAIL"
    with pytest.raises(ValueError, match="Forbidden tool"):
        MCPConfigData.model_validate(raw)


def test_CMP_01_denylist_cannot_be_weakened():
    raw = _raw_config()
    raw["denied_tool_patterns"] = ["SEND"]
    with pytest.raises(ValueError, match="DELETE, TRASH"):
        MCPConfigData.model_validate(raw)


def test_CMP_01_unknown_capability_refused_before_network(composio):
    with pytest.raises(MCPToolRefused):
        composio.client().call("gmail.send_email", {})
    assert composio.methods == []


def test_CMP_02_account_required(composio):
    client = composio.client(gmail="")
    with pytest.raises(MCPAccountNotPinned, match="COMPOSIO_GMAIL_ACCOUNT_ID"):
        client.call("gmail.create_draft", {"recipient_email": TEST_RECIPIENT, "subject": "s", "body": "b"})
    assert composio.methods == []


def test_CMP_02_each_toolkit_uses_its_pinned_account(groww_store, composio):
    PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note", TEST_RECIPIENT)
    accounts = {c.tool: c.account for c in composio.calls}
    assert accounts == {"GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN": DOCS_ACCOUNT, "GMAIL_CREATE_EMAIL_DRAFT": GMAIL_ACCOUNT}


def test_CMP_02_endpoint_keeps_user_id_and_replaces_account():
    url = account_endpoint("https://x.dev/v3/mcp/s?user_id=u&connected_account_id=old", "ca_new")
    assert url == "https://x.dev/v3/mcp/s?user_id=u&connected_account_id=ca_new"


def test_CMP_03_first_publish(groww_store, composio):
    res = PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note", TEST_RECIPIENT)
    state = groww_store.get_publish_state(WEEK)
    assert (state.doc_id, state.doc_url, state.draft_id) == (res.doc_id, res.doc_url, res.draft_id)
    assert state.content_hash == res.content_hash
    assert composio.methods.count("initialize") == 2


def test_CMP_04_same_hash_noop(groww_store, composio):
    publisher = PulsePublisher(groww_store, composio.client())
    publisher.publish_pulse(WEEK, "# Note", TEST_RECIPIENT)
    before = len(composio.methods)
    assert publisher.publish_pulse(WEEK, "# Note", TEST_RECIPIENT).status == "noop"
    assert len(composio.methods) == before


def test_CMP_05_update_in_place(groww_store, composio):
    publisher = PulsePublisher(groww_store, composio.client())
    first = publisher.publish_pulse(WEEK, "# Old note with a longer body", TEST_RECIPIENT)
    composio.calls.clear()
    second = publisher.publish_pulse(WEEK, "# New", TEST_RECIPIENT)
    assert composio.tools_called() == [
        "GOOGLEDOCS_GET_DOCUMENT_BY_ID",
        "GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT",
        "GOOGLEDOCS_UPDATE_DOCUMENT_SECTION_MARKDOWN",
        "GMAIL_UPDATE_DRAFT",
    ]
    assert second.doc_id == first.doc_id and len(composio.documents) == 1
    assert composio.doc_text(first.doc_id) == "# New"
    clear = composio.calls[1].arguments["edit_docs"][0]["deleteContentRange"]["range"]
    assert clear == {"startIndex": 1, "endIndex": len("# Old note with a longer body") + 1}


def test_CMP_05_empty_doc_skips_clear(groww_store, composio):
    publisher = PulsePublisher(groww_store, composio.client())
    first = publisher.publish_pulse(WEEK, "# One", TEST_RECIPIENT)
    composio.documents[first.doc_id]["body"] = ""
    composio.calls.clear()
    publisher.publish_pulse(WEEK, "# Two", TEST_RECIPIENT)
    assert "GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT" not in composio.tools_called()
    assert composio.doc_text(first.doc_id) == "# Two"


def test_CMP_06_draft_recreated(groww_store, composio):
    publisher = PulsePublisher(groww_store, composio.client())
    first = publisher.publish_pulse(WEEK, "# One", TEST_RECIPIENT)
    del composio.drafts[first.draft_id]
    composio.calls.clear()
    second = publisher.publish_pulse(WEEK, "# Two", TEST_RECIPIENT)
    assert composio.tools_called()[-2:] == ["GMAIL_UPDATE_DRAFT", "GMAIL_CREATE_EMAIL_DRAFT"]
    assert second.doc_id == first.doc_id and second.draft_id != first.draft_id
    assert groww_store.get_publish_state(WEEK).draft_id == second.draft_id


def test_CMP_07_connection_expired(groww_store, composio, tmp_path):
    composio.expired_accounts.add(DOCS_ACCOUNT)
    with pytest.raises(MCPConnectionExpired, match="Reconnect Google Docs in Composio") as exc:
        PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note", TEST_RECIPIENT)
    assert "COMPOSIO_GOOGLEDOCS_ACCOUNT_ID" in str(exc.value)
    composio.expired_accounts = {GMAIL_ACCOUNT}
    with pytest.raises(MCPConnectionExpired, match="Reconnect Gmail in Composio"):
        PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note", TEST_RECIPIENT)


def test_CMP_07_pipeline_keeps_markdown_and_reports(groww_store, composio):
    from src.config import get_project_root

    composio.expired_accounts.add(GMAIL_ACCOUNT)
    csv = get_project_root() / "tests" / "fixtures" / "reviews_baseline.csv"
    res = run_full_pipeline(store=groww_store, week_str="2026-11-10", csv_path=csv, mcp_client=composio.client())
    assert res["status"] == "failed"
    assert "Reconnect Gmail in Composio" in res["publish_error"]
    assert (get_project_root() / "outputs" / "groww" / "2026-11-09" / "note.md").is_file()


def test_CMP_07_bad_api_key(groww_store, composio):
    client = ComposioClient(ComposioSettings(url=composio.url, api_key="wrong", accounts=composio.settings().accounts), fast_config())
    with pytest.raises(MCPAuthError, match="COMPOSIO_API_KEY"):
        PulsePublisher(groww_store, client).publish_pulse(WEEK, "# Note", TEST_RECIPIENT)


def test_CMP_08_per_app_documents(pulse_store, composio):
    pulse_store.insert_app(AppRecord(app_key="swiggy", display_name="Swiggy", status="active", play_package_id="in.swiggy.android"))
    client = composio.client()
    groww = PulsePublisher(pulse_store.for_app("groww"), client).publish_pulse(WEEK, "# Groww note", TEST_RECIPIENT)
    swiggy = PulsePublisher(pulse_store.for_app("swiggy"), client).publish_pulse(WEEK, "# Swiggy note", TEST_RECIPIENT)
    assert groww.doc_id != swiggy.doc_id and groww.draft_id != swiggy.draft_id
    assert "Groww" in composio.documents[groww.doc_id]["title"]
    assert "Swiggy" in composio.documents[swiggy.doc_id]["title"]
    assert "Swiggy" in composio.drafts[swiggy.draft_id]["subject"]


def test_CMP_09_draft_body_clean(groww_store, composio):
    res = PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note\n\nBody", TEST_RECIPIENT)
    for call in composio.calls:
        if call.tool.startswith("GMAIL_"):
            assert call.arguments["include_signature"] is False
    draft = composio.drafts[res.draft_id]
    assert draft["body"].endswith(f"Google Doc: {res.doc_url}")
    assert draft["recipient_email"] == TEST_RECIPIENT
    PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note\n\nBody v2", TEST_RECIPIENT)
    update = [c for c in composio.calls if c.tool == "GMAIL_UPDATE_DRAFT"][0]
    assert update.arguments["include_signature"] is False


@pytest.mark.parametrize("missing", list(ENV))
def test_CMP_10_missing_key(missing):
    env = {k: v for k, v in ENV.items() if k != missing}
    with pytest.raises(MCPMissingSetting, match=missing):
        ComposioClient.from_env(load_mcp_config("config/mcp.yaml"), env)


def test_CMP_10_pipeline_fails_before_any_run(groww_store, monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(MCPMissingSetting, match="COMPOSIO_API_KEY"):
        run_full_pipeline(store=groww_store, week_str="2026-11-10")
    with groww_store.connector.session() as s:
        assert s.fetchone("SELECT COUNT(*) AS n FROM runs")["n"] == 0


def test_rpc_body_accepts_json_and_sse():
    assert decode_rpc_body('{"jsonrpc":"2.0","id":3,"result":{}}', 3)["result"] == {}
    sse = 'event: message\ndata: {"jsonrpc":"2.0","method":"notifications/progress"}\n\ndata: {"jsonrpc":"2.0","id":4,"result":{"x":1}}\n'
    assert decode_rpc_body(sse, 4)["result"] == {"x": 1}


def test_plain_json_transport(groww_store, composio):
    composio.sse = False
    assert PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note", TEST_RECIPIENT).status == "published"


def test_expired_session_is_renewed(groww_store, composio):
    publisher = PulsePublisher(groww_store, composio.client())
    publisher.publish_pulse(WEEK, "# One", TEST_RECIPIENT)
    composio.sessions.clear()
    assert publisher.publish_pulse(WEEK, "# Two", TEST_RECIPIENT).status == "published"
