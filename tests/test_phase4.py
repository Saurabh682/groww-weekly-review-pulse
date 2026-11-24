import pytest

from src.config import get_project_root
from src.mcp.errors import MCPConnectionError, MCPError, MCPMalformedResponse
from src.mcp.composio import ComposioClient, ComposioSettings
from src.mcp.publisher import DocsPublisher, DraftPublisher, PulsePublisher, draft_body
from tests.conftest import TEST_RECIPIENT
from tests.support.composio_server import fast_config

WEEK = "2026-11-10"


@pytest.fixture
def publisher(groww_store, composio):
    return PulsePublisher(store=groww_store, client=composio.client())


def test_MCP_01_normal_first_publish(publisher, composio):
    res = publisher.publish_pulse(WEEK, "# Note content\n\nGoogle Play reviews.", TEST_RECIPIENT)
    assert res.status == "published"
    assert res.doc_url.startswith("https://docs.google.com/document/d/")
    assert res.draft_id in composio.drafts
    assert composio.tools_called() == ["GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN", "GMAIL_CREATE_EMAIL_DRAFT"]


def test_MCP_08_same_hash_noop(publisher, composio):
    md = "# Note\n\nGoogle Play reviews."
    publisher.publish_pulse(WEEK, md, TEST_RECIPIENT)
    calls = len(composio.calls)
    res = publisher.publish_pulse(WEEK, md, TEST_RECIPIENT)
    assert res.status == "noop"
    assert "Content hash unchanged" in res.message
    assert len(composio.calls) == calls


def test_MCP_09_changed_content_update(publisher, composio):
    first = publisher.publish_pulse(WEEK, "# Note v1\n\nGoogle Play reviews.", TEST_RECIPIENT)
    second = publisher.publish_pulse(WEEK, "# Note v2 (modified)\n\nGoogle Play reviews.", TEST_RECIPIENT)
    assert (second.doc_id, second.draft_id) == (first.doc_id, first.draft_id)
    assert composio.doc_text(first.doc_id) == "# Note v2 (modified)\n\nGoogle Play reviews."
    assert len(composio.documents) == 1 and len(composio.drafts) == 1


def test_MCP_06_partial_failure_resume(groww_store, composio):
    composio.failing_tools.add("GMAIL_CREATE_EMAIL_DRAFT")
    with pytest.raises(MCPError):
        PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note\n\nGoogle Play reviews.", TEST_RECIPIENT)
    state = groww_store.get_publish_state(WEEK)
    assert state.doc_id and state.draft_id is None and state.content_hash is None

    composio.failing_tools.clear()
    res = PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "# Note\n\nGoogle Play reviews.", TEST_RECIPIENT)
    assert res.doc_id == state.doc_id
    assert len(composio.documents) == 1 and len(composio.drafts) == 1


def test_MCP_06_failed_draft_update_never_freezes_stale_draft(groww_store, composio):
    publisher = PulsePublisher(groww_store, composio.client())
    first = publisher.publish_pulse(WEEK, "# v1", TEST_RECIPIENT)
    composio.failing_tools.add("GMAIL_UPDATE_DRAFT")
    with pytest.raises(MCPError):
        publisher.publish_pulse(WEEK, "# v2", TEST_RECIPIENT)
    composio.failing_tools.clear()
    retry = publisher.publish_pulse(WEEK, "# v2", TEST_RECIPIENT)
    assert retry.status == "published"
    assert composio.drafts[first.draft_id]["body"].startswith("# v2")
    reverted = publisher.publish_pulse(WEEK, "# v1", TEST_RECIPIENT)
    assert reverted.status == "published"
    assert composio.doc_text(first.doc_id) == "# v1"


def test_MCP_10_doc_deleted_externally(publisher, composio):
    first = publisher.publish_pulse(WEEK, "# Note v1", TEST_RECIPIENT)
    del composio.documents[first.doc_id]
    second = publisher.publish_pulse(WEEK, "# Note v2", TEST_RECIPIENT)
    assert second.doc_id != first.doc_id
    assert composio.doc_text(second.doc_id) == "# Note v2"
    assert second.doc_url in composio.drafts[second.draft_id]["body"]


def test_MCP_11_draft_deleted_or_sent(publisher, composio):
    first = publisher.publish_pulse(WEEK, "# Note v1", TEST_RECIPIENT)
    del composio.drafts[first.draft_id]
    second = publisher.publish_pulse(WEEK, "# Note v2", TEST_RECIPIENT)
    assert second.draft_id != first.draft_id
    assert composio.drafts[second.draft_id]["is_sent"] is False


def test_MCP_04_unreachable_retries_then_fails(groww_store, composio):
    composio.http_failures.extend([503, 503, 503])
    with pytest.raises(MCPConnectionError):
        PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "Content", TEST_RECIPIENT)
    assert composio.calls == []


def test_MCP_04_closed_port_is_connection_error(groww_store, composio):
    url = composio.url
    composio.stop()
    config = fast_config()
    single_attempt = config.model_copy(update={"policy": config.policy.model_copy(update={"max_retries": 1})})
    client = ComposioClient(ComposioSettings(url=url, api_key="k", accounts={"googledocs": "a", "gmail": "b"}), single_attempt)
    with pytest.raises(MCPConnectionError):
        PulsePublisher(groww_store, client).publish_pulse(WEEK, "Content", TEST_RECIPIENT)


def test_MCP_04_transient_failure_recovers(publisher, composio):
    composio.http_failures.extend([502])
    assert publisher.publish_pulse(WEEK, "Content", TEST_RECIPIENT).status == "published"


def test_MCP_14_rate_limit_is_bounded(groww_store, composio):
    from src.mcp.errors import MCPRateLimitError

    composio.http_failures.extend([429, 429, 429])
    with pytest.raises(MCPRateLimitError):
        PulsePublisher(groww_store, composio.client()).publish_pulse(WEEK, "Content", TEST_RECIPIENT)


def test_MCP_13_malformed_success_response(composio):
    composio.malformed_tools.add("GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN")
    with pytest.raises(MCPMalformedResponse, match="missing doc_id"):
        DocsPublisher(composio.client()).upsert("Title", "Content", None, None)


def test_MCP_15_recipient_validation(groww_store, composio):
    publisher = PulsePublisher(groww_store, composio.client())
    for bad in ("", "not-an-email"):
        with pytest.raises(ValueError, match="MCP-15"):
            publisher.publish_pulse(WEEK, "Content", bad)
    assert composio.calls == []


def test_MCP_17_drafts_never_sent(publisher, composio):
    res = publisher.publish_pulse(WEEK, "Body text", TEST_RECIPIENT)
    assert composio.drafts[res.draft_id]["is_sent"] is False
    assert not any("SEND" in tool for tool in composio.tools_called())


def test_MCP_18_no_google_sdk_or_rest():
    forbidden = ["googleapiclient", "google.oauth2", "google.auth", "from google.cloud import docs", "googleapis.com"]
    for py_file in get_project_root().glob("src/**/*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in forbidden:
            assert pattern not in content, f"{pattern} found in {py_file}"


def test_MCP_24_pre_publish_pii_gate(groww_store, composio):
    with pytest.raises(ValueError, match="MCP-24"):
        PulsePublisher(groww_store, composio.client()).publish_pulse(
            WEEK, "# Note\n\nCustomer phone: +91 98765 43210", TEST_RECIPIENT
        )
    assert composio.calls == []


def test_MCP_25_doc_link_in_email(composio):
    doc_url = "https://docs.google.com/document/d/doc_sample_123/edit"
    draft_id = DraftPublisher(composio.client()).upsert(TEST_RECIPIENT, "Subject", draft_body("Body content", doc_url), None)
    assert f"Google Doc: {doc_url}" in composio.drafts[draft_id]["body"]


def test_MCP_26_consistent_week_dates(publisher, composio):
    res = publisher.publish_pulse(WEEK, "Content", TEST_RECIPIENT)
    assert WEEK in composio.documents[res.doc_id]["title"]
    assert WEEK in composio.drafts[res.draft_id]["subject"]
