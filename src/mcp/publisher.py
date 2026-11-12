"""Publisher engine for Google Docs and Gmail drafts via Model Context Protocol (MCP) (Phase 4).

Guarantees:
- Never sends email: draft-only (MCP-17).
- Pre-publish PII gate on email subject and body (MCP-24).
- Idempotent publish with content hash tracking in publish_state (MCP-08, MCP-09).
- Partial failure resume (Docs succeeds, Gmail fails -> resume at Gmail, MCP-06).
- Versioned fallbacks when update tools are unsupported (MCP-02, MCP-03).
- Clean recreation when docs/drafts are deleted externally (MCP-10, MCP-11).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Dict, Optional, Tuple

from src.clean.pii import scrub_pii
from src.mcp.capabilities import MCPConfigData, resolve_capability
from src.mcp.client import MCPClient, MCPError, MCPToolNotFoundError
from src.store.db import Database


@dataclass
class PublishResult:
    """Outcome of publishing a weekly review pulse note."""
    status: str  # "published", "noop", "failed"
    week_start: str
    doc_id: Optional[str] = None
    doc_url: Optional[str] = None
    draft_id: Optional[str] = None
    content_hash: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "week_start": self.week_start,
            "doc_id": self.doc_id,
            "doc_url": self.doc_url,
            "draft_id": self.draft_id,
            "content_hash": self.content_hash,
            "message": self.message
        }


class DocsPublisher:
    """Manages publishing weekly pulse notes to Google Docs via MCP."""

    def __init__(self, client: MCPClient, mcp_config: MCPConfigData):
        self.client = client
        self.mcp_config = mcp_config

    def upsert_pulse(
        self,
        week_start: str,
        note_markdown: str,
        existing_doc_id: Optional[str] = None,
        existing_doc_url: Optional[str] = None,
        version: int = 1
    ) -> Tuple[str, str]:
        """Create or update Google Doc. Returns (doc_id, doc_url)."""
        base_title = f"Groww Weekly Review Pulse: Week of {week_start}"
        
        # Check if update tool is supported and existing_doc_id is valid
        if existing_doc_id:
            try:
                target_update = resolve_capability(self.mcp_config, "docs.update")
                res = self.client.call_tool(
                    server=target_update.server,
                    tool=target_update.tool,
                    arguments={"doc_id": existing_doc_id, "content": note_markdown}
                )
                doc_url = res.get("doc_url") or existing_doc_url or f"https://docs.google.com/document/d/{existing_doc_id}/edit"
                return existing_doc_id, doc_url
            except (MCPToolNotFoundError, KeyError, PermissionError):
                # MCP-02: docs.update unsupported -> fall back to versioned create
                return self.upsert_pulse(
                    week_start=week_start,
                    note_markdown=note_markdown,
                    existing_doc_id=None,
                    version=version + 1
                )
            except MCPError as exc:
                # MCP-10: doc deleted externally
                if "not found" in str(exc).lower():
                    return self.upsert_pulse(
                        week_start=week_start,
                        note_markdown=note_markdown,
                        existing_doc_id=None,
                        version=version
                    )
                raise

        # Create new Doc
        title = f"{base_title} (v{version})" if version > 1 else base_title
        target_create = resolve_capability(self.mcp_config, "docs.create")
        res = self.client.call_tool(
            server=target_create.server,
            tool=target_create.tool,
            arguments={"title": title, "content": note_markdown}
        )

        doc_id = res.get("doc_id")
        doc_url = res.get("doc_url")
        if not doc_id or not doc_url:
            # MCP-13: Malformed response
            raise MCPError("MCP docs.create returned success but missing doc_id or doc_url.")

        return str(doc_id), str(doc_url)


class DraftPublisher:
    """Manages creating unsent Gmail drafts via MCP."""

    def __init__(self, client: MCPClient, mcp_config: MCPConfigData):
        self.client = client
        self.mcp_config = mcp_config

    def _validate_recipient(self, recipient: str) -> None:
        """Validate recipient address (MCP-15, MCP-16)."""
        if not recipient or not recipient.strip():
            raise ValueError("MCP-15: Recipient email address is missing or empty.")
            
        # Basic email syntax check
        email_pattern = r"^[\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, recipient.strip()):
            raise ValueError(f"MCP-15: Malformed recipient email address: '{recipient}'.")

    def upsert_draft(
        self,
        week_start: str,
        to_address: str,
        note_markdown: str,
        doc_url: Optional[str] = None,
        existing_draft_id: Optional[str] = None,
        revision: int = 1
    ) -> str:
        """Create or update unsent Gmail draft with Doc link. Returns draft_id."""
        self._validate_recipient(to_address)

        # Subject line (MCP-26)
        subject = f"Groww Weekly Review Pulse | Week of {week_start}"
        if revision > 1:
            subject += f" [Rev {revision}]"

        # Body formatting with doc link (MCP-25)
        doc_mention = f"Google Doc: {doc_url}" if doc_url else "Google Doc link: unavailable"
        full_body = f"{note_markdown}\n\n---\n{doc_mention}"

        # PRE-PUBLISH PII GATE (MCP-24)
        # Mask official Google Doc link so legitimate doc_url (MCP-25) is not blocked by generic URL filter
        body_to_scan = full_body
        if doc_url:
            body_to_scan = body_to_scan.replace(doc_url, "[SYSTEM_DOC_URL]")

        pii_check_subject = scrub_pii(subject)
        pii_check_body = scrub_pii(body_to_scan)
        if pii_check_subject.pii_found or pii_check_body.pii_found:
            total_redactions = pii_check_subject.redaction_count + pii_check_body.redaction_count
            raise ValueError(
                f"MCP-24: Pre-publish PII gate blocked draft creation! "
                f"Found {total_redactions} PII occurrence(s) in draft content."
            )

        # Try update if existing draft ID is present
        if existing_draft_id:
            try:
                target_update = resolve_capability(self.mcp_config, "gmail.update_draft")
                res = self.client.call_tool(
                    server=target_update.server,
                    tool=target_update.tool,
                    arguments={"draft_id": existing_draft_id, "subject": subject, "body": full_body}
                )
                draft_id = res.get("draft_id") or existing_draft_id
                return str(draft_id)
            except (MCPToolNotFoundError, KeyError, PermissionError):
                # MCP-03: update_draft unsupported -> fall back to revision draft
                return self.upsert_draft(
                    week_start=week_start,
                    to_address=to_address,
                    note_markdown=note_markdown,
                    doc_url=doc_url,
                    existing_draft_id=None,
                    revision=revision + 1
                )
            except MCPError as exc:
                # MCP-11: draft deleted or already sent
                if "not found" in str(exc).lower() or "sent" in str(exc).lower():
                    return self.upsert_draft(
                        week_start=week_start,
                        to_address=to_address,
                        note_markdown=note_markdown,
                        doc_url=doc_url,
                        existing_draft_id=None,
                        revision=revision
                    )
                raise

        # Create new draft (MCP-17: NEVER SEND)
        target_create = resolve_capability(self.mcp_config, "gmail.create_draft")
        res = self.client.call_tool(
            server=target_create.server,
            tool=target_create.tool,
            arguments={"to": to_address.strip(), "subject": subject, "body": full_body}
        )

        draft_id = res.get("draft_id")
        if not draft_id:
            # MCP-13: Malformed response
            raise MCPError("MCP gmail.create_draft returned success but missing draft_id.")

        return str(draft_id)


class PulsePublisher:
    """Coordinates publishing pulse notes to Google Docs and Gmail drafts with idempotency."""

    def __init__(
        self,
        database: Database,
        mcp_config: MCPConfigData,
        client: Optional[MCPClient] = None
    ):
        self.database = database
        self.mcp_config = mcp_config
        self.client = client or MCPClient(
            max_retries=mcp_config.policy.max_retries,
            timeout_seconds=mcp_config.policy.timeout_seconds
        )
        self.docs_pub = DocsPublisher(self.client, mcp_config)
        self.draft_pub = DraftPublisher(self.client, mcp_config)

    def publish_pulse(
        self,
        week_start: str,
        note_markdown: str,
        recipient_email: str = "self@groww-pulse.local"
    ) -> PublishResult:
        """Publish weekly review pulse note idempotently (MCP-01..26)."""
        content_hash = hashlib.sha256(note_markdown.encode("utf-8")).hexdigest()

        # 1. Check existing publish state (MCP-08, MCP-09, MCP-06)
        existing_doc_id: Optional[str] = None
        existing_doc_url: Optional[str] = None
        existing_draft_id: Optional[str] = None
        existing_hash: Optional[str] = None

        with self.database.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM publish_state WHERE week_start = ?", (week_start,))
            row = c.fetchone()
            if row:
                existing_doc_id = row["doc_id"]
                existing_doc_url = row["doc_url"]
                existing_draft_id = row["draft_id"]
                existing_hash = row["content_hash"]

        # MCP-08: Same hash no-op
        if existing_hash == content_hash and existing_doc_id and existing_draft_id:
            return PublishResult(
                status="noop",
                week_start=week_start,
                doc_id=existing_doc_id,
                doc_url=existing_doc_url,
                draft_id=existing_draft_id,
                content_hash=content_hash,
                message="Content hash unchanged. Publish skipped (idempotent no-op)."
            )

        # 2. Upsert Google Doc
        # Note: If existing_doc_id exists from a previous run where Gmail failed,
        # we reuse it (MCP-06: Partial failure resume).
        doc_id, doc_url = self.docs_pub.upsert_pulse(
            week_start=week_start,
            note_markdown=note_markdown,
            existing_doc_id=existing_doc_id,
            existing_doc_url=existing_doc_url
        )

        # Save intermediate doc state so partial failure can resume cleanly
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.database.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO publish_state (
                    week_start, doc_id, doc_url, draft_id, content_hash, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (week_start, doc_id, doc_url, existing_draft_id, content_hash, now_iso))

        # 3. Upsert Gmail Draft (MCP-25: includes doc_url; MCP-24: PII gate)
        draft_id = self.draft_pub.upsert_draft(
            week_start=week_start,
            to_address=recipient_email,
            note_markdown=note_markdown,
            doc_url=doc_url,
            existing_draft_id=existing_draft_id
        )

        # 4. Save final completed publish state
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.database.get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO publish_state (
                    week_start, doc_id, doc_url, draft_id, content_hash, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (week_start, doc_id, doc_url, draft_id, content_hash, now_iso))

        return PublishResult(
            status="published",
            week_start=week_start,
            doc_id=doc_id,
            doc_url=doc_url,
            draft_id=draft_id,
            content_hash=content_hash,
            message="Successfully published to Google Doc and Gmail draft."
        )
