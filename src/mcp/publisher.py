import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from src.clean.pii import scrub_pii
from src.mcp.composio import ToolCaller
from src.mcp.errors import MCPMalformedResponse, MCPNotFoundError
from src.note.titles import pulse_doc_title, pulse_email_subject
from src.store.models import PublishStateRecord
from src.store.store import AppStore

DOC_URL_TEMPLATE = "https://docs.google.com/document/d/{}/edit"
DOC_URL_MASK = "[SYSTEM_DOC_URL]"
EMAIL_PATTERN = re.compile(r"^[\w.+\-]+@[\w\-]+(\.[\w\-]+)*\.[A-Za-z]{2,}$")
FIRST_BODY_INDEX = 1


@dataclass
class PublishResult:
    status: str
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
            "message": self.message,
        }


def response_value(data: Dict[str, Any], *keys: str) -> Optional[str]:
    nested = data.get("response_data")
    for source in (data, nested if isinstance(nested, dict) else {}):
        for key in keys:
            value = source.get(key)
            if isinstance(value, (str, int)) and str(value).strip():
                return str(value)
    return None


def document_end_index(document: Dict[str, Any]) -> int:
    nested = document.get("response_data")
    body = document.get("body") or (nested.get("body") if isinstance(nested, dict) else None) or {}
    elements = body.get("content") or []
    if not elements:
        raise MCPMalformedResponse("docs.get returned no body content; cannot replace the Doc safely.")
    return max(int(e.get("endIndex", FIRST_BODY_INDEX)) for e in elements if isinstance(e, dict))


def validate_recipient(recipient: str) -> str:
    value = (recipient or "").strip()
    if not value:
        raise ValueError("MCP-15: Recipient email address is missing or empty.")
    if not EMAIL_PATTERN.match(value):
        raise ValueError("MCP-15: Recipient email address is malformed.")
    return value


def pii_gate(*texts: str) -> None:
    found = [scrub_pii(t) for t in texts]
    hits = sum(r.redaction_count for r in found if r.pii_found)
    if hits:
        raise ValueError(f"MCP-24: Pre-publish PII gate blocked publishing. Found {hits} PII occurrence(s).")


def draft_body(note_markdown: str, doc_url: str) -> str:
    return f"{note_markdown}\n\n---\nGoogle Doc: {doc_url}"


class DocsPublisher:
    def __init__(self, client: ToolCaller):
        self.client = client

    def upsert(self, title: str, markdown: str, doc_id: Optional[str], doc_url: Optional[str]) -> Tuple[str, str]:
        if not doc_id:
            return self._create(title, markdown)
        try:
            document = self.client.call("docs.get", {"id": doc_id})
        except MCPNotFoundError:
            return self._create(title, markdown)
        end_index = document_end_index(document)
        if end_index - 1 > FIRST_BODY_INDEX:
            self.client.call("docs.clear", {
                "document_id": doc_id,
                "edit_docs": [{"deleteContentRange": {"range": {"startIndex": FIRST_BODY_INDEX, "endIndex": end_index - 1}}}],
            })
        self.client.call("docs.write", {"document_id": doc_id, "markdown_text": markdown})
        url = response_value(document, "document_url", "display_url") or doc_url or DOC_URL_TEMPLATE.format(doc_id)
        return doc_id, url

    def _create(self, title: str, markdown: str) -> Tuple[str, str]:
        data = self.client.call("docs.create", {"title": title, "markdown_text": markdown})
        doc_id = response_value(data, "documentId", "document_id", "id")
        if not doc_id:
            raise MCPMalformedResponse("docs.create returned success but missing doc_id (MCP-13).")
        url = response_value(data, "display_url", "document_url", "url") or DOC_URL_TEMPLATE.format(doc_id)
        return doc_id, url


class DraftPublisher:
    def __init__(self, client: ToolCaller):
        self.client = client

    def upsert(self, recipient: str, subject: str, body: str, draft_id: Optional[str]) -> str:
        fields = {
            "recipient_email": validate_recipient(recipient),
            "subject": subject,
            "body": body,
            "include_signature": False,
        }
        if draft_id:
            try:
                data = self.client.call("gmail.update_draft", {"draft_id": draft_id, **fields})
            except MCPNotFoundError:
                return self._create(fields)
            return response_value(data, "id", "draft_id") or draft_id
        return self._create(fields)

    def _create(self, fields: Dict[str, Any]) -> str:
        data = self.client.call("gmail.create_draft", {**fields, "is_html": False})
        new_id = response_value(data, "id", "draft_id")
        if not new_id:
            raise MCPMalformedResponse("gmail.create_draft returned success but missing draft_id (MCP-13).")
        return new_id


class PulsePublisher:
    def __init__(self, store: AppStore, client: ToolCaller):
        self.store = store
        self.docs = DocsPublisher(client)
        self.drafts = DraftPublisher(client)

    def publish_pulse(self, week_start: str, note_markdown: str, recipient_email: str) -> PublishResult:
        content_hash = hashlib.sha256(note_markdown.encode("utf-8")).hexdigest()
        state = self.store.get_publish_state(week_start) or PublishStateRecord(week_start=week_start)
        if state.content_hash == content_hash and state.doc_id and state.draft_id:
            return PublishResult(
                status="noop", week_start=week_start, doc_id=state.doc_id, doc_url=state.doc_url,
                draft_id=state.draft_id, content_hash=content_hash,
                message="Content hash unchanged. Publish skipped (idempotent no-op).",
            )
        recipient = validate_recipient(recipient_email)
        app_name = self.store.app.display_name
        title = pulse_doc_title(app_name, week_start)
        subject = pulse_email_subject(app_name, week_start)
        pii_gate(title, subject, note_markdown)

        doc_id, doc_url = self.docs.upsert(title, note_markdown, state.doc_id, state.doc_url)
        self.store.save_publish_state(PublishStateRecord(
            week_start=week_start, doc_id=doc_id, doc_url=doc_url, draft_id=state.draft_id, content_hash=None,
        ))

        body = draft_body(note_markdown, doc_url)
        pii_gate(subject, body.replace(doc_url, DOC_URL_MASK))
        draft_id = self.drafts.upsert(recipient, subject, body, state.draft_id)
        self.store.save_publish_state(PublishStateRecord(
            week_start=week_start, doc_id=doc_id, doc_url=doc_url, draft_id=draft_id, content_hash=content_hash,
        ))
        return PublishResult(
            status="published", week_start=week_start, doc_id=doc_id, doc_url=doc_url,
            draft_id=draft_id, content_hash=content_hash,
            message="Published to the Google Doc and the Gmail draft.",
        )
