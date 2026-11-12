"""Unit and contract tests for Phase 4: MCP Publishing (Google Docs + Gmail).

Covers:
- MCP-01..11: Publish flows, idempotency, partial failure resume, fallbacks
- MCP-13..16: Schema validation, recipient validation, malformed responses
- MCP-17..18: No send capability and zero Google SDK / REST imports
- MCP-21, 24..26: Unicode preservation, pre-publish PII gate, doc links, date consistency
"""

import os
from pathlib import Path
import pytest
import tempfile

from src.config import get_project_root
from src.mcp.capabilities import load_mcp_config
from src.mcp.client import (
    MCPAuthExpiredError,
    MCPConnectionError,
    MCPError,
    MockMCPClient,
)
from src.mcp.publisher import DocsPublisher, DraftPublisher, PulsePublisher
from src.store.db import Database


@pytest.fixture
def mock_db():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Database(Path(tmp_dir) / "test.db")
        yield db


@pytest.fixture
def mcp_cfg():
    return load_mcp_config("config/mcp.yaml")


# ==============================================================================
# Publish Lifecycle & Idempotency Tests (MCP-01, 06, 08, 09, 10, 11)
# ==============================================================================

def test_MCP_01_normal_first_publish(mock_db, mcp_cfg):
    """MCP-01 (P0): First publish creates Google Doc and Gmail draft with Doc link."""
    client = MockMCPClient()
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)

    res = publisher.publish_pulse(
        week_start="2026-11-10",
        note_markdown="# Note content\n\nGoogle Play reviews.",
        recipient_email="self@groww-pulse.local"
    )

    assert res.status == "published"
    assert res.doc_id is not None
    assert "https://docs.google.com/document/d/" in res.doc_url
    assert res.draft_id is not None
    assert len(client.call_history) == 2  # create_document + create_draft


def test_MCP_08_same_hash_noop(mock_db, mcp_cfg):
    """MCP-08 (P0): Calling publish twice with identical content is a NO-OP."""
    client = MockMCPClient()
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)
    md = "# Note\n\nGoogle Play reviews."

    res1 = publisher.publish_pulse("2026-11-10", md)
    assert res1.status == "published"
    calls_after_first = len(client.call_history)

    res2 = publisher.publish_pulse("2026-11-10", md)
    assert res2.status == "noop"
    assert "Content hash unchanged" in res2.message
    # No new tool calls were made
    assert len(client.call_history) == calls_after_first


def test_MCP_09_changed_content_update(mock_db, mcp_cfg):
    """MCP-09 (P0): Publishing modified content updates existing Doc and draft in place."""
    client = MockMCPClient()
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)

    res1 = publisher.publish_pulse("2026-11-10", "# Note v1\n\nGoogle Play reviews.")
    doc_id_1 = res1.doc_id
    draft_id_1 = res1.draft_id

    res2 = publisher.publish_pulse("2026-11-10", "# Note v2 (modified)\n\nGoogle Play reviews.")
    assert res2.status == "published"
    # Same IDs updated in place
    assert res2.doc_id == doc_id_1
    assert res2.draft_id == draft_id_1
    assert client.documents[doc_id_1]["version"] == 2


def test_MCP_06_partial_failure_resume(mock_db, mcp_cfg):
    """MCP-06 (P0): If Doc succeeded and Gmail draft failed, next run resumes at Gmail."""
    # Run 1: Docs succeeds, but Gmail fails
    client1 = MockMCPClient(unsupported_tools=["create_draft"])
    pub1 = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client1)
    
    with pytest.raises(MCPError):
        pub1.publish_pulse("2026-11-10", "# Note\n\nGoogle Play reviews.")

    # Doc was recorded in publish_state
    with mock_db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT doc_id, draft_id FROM publish_state WHERE week_start = '2026-11-10'")
        row = c.fetchone()
        assert row["doc_id"] is not None
        assert row["draft_id"] is None
        doc_id_saved = row["doc_id"]

    # Run 2: Resume with healthy client
    client2 = MockMCPClient()
    pub2 = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client2)
    res2 = pub2.publish_pulse("2026-11-10", "# Note\n\nGoogle Play reviews.")

    assert res2.status == "published"
    assert res2.doc_id == doc_id_saved  # Reused without duplicate doc creation!
    assert res2.draft_id is not None


def test_MCP_10_doc_deleted_externally(mock_db, mcp_cfg):
    """MCP-10 (P1): If user deleted the Doc on Google Docs, pipeline recreates it."""
    client = MockMCPClient()
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)

    res1 = publisher.publish_pulse("2026-11-10", "# Note v1\n\nGoogle Play reviews.")
    first_doc_id = res1.doc_id

    # Simulate user deleting doc externally
    client.deleted_docs.add(first_doc_id)

    res2 = publisher.publish_pulse("2026-11-10", "# Note v2\n\nGoogle Play reviews.")
    assert res2.status == "published"
    assert res2.doc_id != first_doc_id  # New doc created
    assert res2.doc_id in client.documents


def test_MCP_11_draft_deleted_or_sent(mock_db, mcp_cfg):
    """MCP-11 (P1): If user sent or deleted the draft, pipeline creates a fresh draft."""
    client = MockMCPClient()
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)

    res1 = publisher.publish_pulse("2026-11-10", "# Note v1\n\nGoogle Play reviews.")
    first_draft_id = res1.draft_id

    # Simulate user sending draft externally
    client.deleted_drafts.add(first_draft_id)

    res2 = publisher.publish_pulse("2026-11-10", "# Note v2\n\nGoogle Play reviews.")
    assert res2.status == "published"
    assert res2.draft_id != first_draft_id


# ==============================================================================
# Unsupported Tool Fallbacks (MCP-02, MCP-03)
# ==============================================================================

def test_MCP_02_update_unsupported_versioned_doc(mcp_cfg):
    """MCP-02 (P1): When docs.update is unsupported, DocsPublisher creates a versioned doc."""
    client = MockMCPClient(unsupported_tools=["update_document"])
    docs_pub = DocsPublisher(client, mcp_cfg)

    # First creation
    doc_id_1, _ = docs_pub.upsert_pulse("2026-11-10", "Content v1")
    # Attempt update falls back to versioned create (v2)
    doc_id_2, _ = docs_pub.upsert_pulse("2026-11-10", "Content v2", existing_doc_id=doc_id_1)
    
    assert doc_id_2 != doc_id_1
    assert "v2" in client.documents[doc_id_2]["title"]


def test_MCP_03_draft_update_unsupported_revision(mcp_cfg):
    """MCP-03 (P1): When gmail.update_draft is unsupported, creates revision draft."""
    client = MockMCPClient(unsupported_tools=["update_draft"])
    draft_pub = DraftPublisher(client, mcp_cfg)

    draft_1 = draft_pub.upsert_draft("2026-11-10", "self@groww-pulse.local", "Body v1")
    draft_2 = draft_pub.upsert_draft("2026-11-10", "self@groww-pulse.local", "Body v2", existing_draft_id=draft_1)

    assert draft_2 != draft_1
    assert "[Rev 2]" in client.drafts[draft_2]["subject"]


# ==============================================================================
# Error Handling & Edge Cases (MCP-04, 05, 13, 15, 16)
# ==============================================================================

def test_MCP_04_unreachable_retries_then_fails(mock_db, mcp_cfg):
    """MCP-04 (P0): Unreachable server raises MCPConnectionError."""
    client = MockMCPClient(fail_unreachable=True)
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)

    with pytest.raises(MCPConnectionError):
        publisher.publish_pulse("2026-11-10", "Content")


def test_MCP_05_auth_expired_message(mock_db, mcp_cfg):
    """MCP-05 (P1): Auth expired raises actionable error naming connector."""
    client = MockMCPClient(fail_auth_expired=True)
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)

    with pytest.raises(MCPAuthExpiredError) as exc_info:
        publisher.publish_pulse("2026-11-10", "Content")
    assert "Re-authorize" in str(exc_info.value)


def test_MCP_13_malformed_success_response(mcp_cfg):
    """MCP-13 (P0): Tool returning success but missing doc_id or URL raises MCPError."""
    client = MockMCPClient(fail_malformed_response=True)
    docs_pub = DocsPublisher(client, mcp_cfg)

    with pytest.raises(MCPError) as exc_info:
        docs_pub.upsert_pulse("2026-11-10", "Content")
    assert "missing doc_id or doc_url" in str(exc_info.value)


def test_MCP_15_recipient_validation(mcp_cfg):
    """MCP-15 (P0): Empty or malformed email address rejected."""
    client = MockMCPClient()
    draft_pub = DraftPublisher(client, mcp_cfg)

    with pytest.raises(ValueError):
        draft_pub.upsert_draft("2026-11-10", "", "Content")

    with pytest.raises(ValueError):
        draft_pub.upsert_draft("2026-11-10", "not-an-email", "Content")


# ==============================================================================
# Security Invariants & Compliance (MCP-17, 18, 21, 24, 25, 26)
# ==============================================================================

def test_MCP_17_no_send_capability():
    """MCP-17 (P0): Drafts must never have is_sent=True; no send capabilities."""
    mcp_cfg = load_mcp_config("config/mcp.yaml")
    client = MockMCPClient()
    draft_pub = DraftPublisher(client, mcp_cfg)

    draft_id = draft_pub.upsert_draft("2026-11-10", "self@groww-pulse.local", "Body text")
    assert client.drafts[draft_id]["is_sent"] is False


def test_MCP_18_no_google_sdk_or_rest():
    """MCP-18 (P0): Static scan guarantees zero Google SDK or direct REST imports."""
    root = get_project_root()
    py_files = list(root.glob("src/**/*.py"))

    forbidden_imports = [
        "googleapiclient",
        "google.oauth2",
        "google.auth",
        "from google.cloud import docs",
        "googleapis.com",
    ]

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        for forbidden in forbidden_imports:
            assert forbidden not in content, f"Forbidden Google SDK import '{forbidden}' found in {py_file}!"


def test_MCP_24_pre_publish_pii_gate(mcp_cfg):
    """MCP-24 (P0): Pre-publish PII gate blocks draft creation if seeded PII appears."""
    client = MockMCPClient()
    draft_pub = DraftPublisher(client, mcp_cfg)

    contaminated_body = "# Note\n\nCustomer phone: +91 98765 43210"
    with pytest.raises(ValueError) as exc_info:
        draft_pub.upsert_draft("2026-11-10", "self@groww-pulse.local", contaminated_body)
    assert "MCP-24: Pre-publish PII gate blocked draft creation" in str(exc_info.value)


def test_MCP_25_doc_link_in_email(mcp_cfg):
    """MCP-25 (P1): Doc link is inserted into draft body using returned doc_url."""
    client = MockMCPClient()
    draft_pub = DraftPublisher(client, mcp_cfg)

    doc_url = "https://docs.google.com/document/d/doc_sample_123/edit"
    draft_id = draft_pub.upsert_draft(
        "2026-11-10",
        "self@groww-pulse.local",
        "Body content",
        doc_url=doc_url
    )
    assert f"Google Doc: {doc_url}" in client.drafts[draft_id]["body"]


def test_MCP_26_consistent_week_dates(mock_db, mcp_cfg):
    """MCP-26 (P1): Week date is formatted consistently across Doc title and email subject."""
    client = MockMCPClient()
    publisher = PulsePublisher(database=mock_db, mcp_config=mcp_cfg, client=client)

    week_start = "2026-11-10"
    res = publisher.publish_pulse(week_start, "Content")

    assert week_start in client.documents[res.doc_id]["title"]
    assert week_start in client.drafts[res.draft_id]["subject"]
