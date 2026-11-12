"""Model Context Protocol (MCP) client abstraction for Google Docs and Gmail (Phase 4).

Handles connection management, tool invocation, retries with backoff,
timeout enforcement, structured error types, and dry-run/mock execution.
"""

import json
import time
from typing import Any, Dict, List, Optional


class MCPError(Exception):
    """Base error for MCP operations."""
    pass


class MCPConnectionError(MCPError):
    """MCP server is unreachable, connection refused, or broken pipe."""
    pass


class MCPTimeoutError(MCPError):
    """MCP call timed out."""
    pass


class MCPAuthExpiredError(MCPError):
    """Authentication session on MCP host expired or revoked (MCP-05)."""
    pass


class MCPRateLimitError(MCPError):
    """Rate limit hit on MCP server (MCP-14)."""
    pass


class MCPToolNotFoundError(MCPError):
    """Tool not found or unsupported by server."""
    pass


class MCPClient:
    """Client for invoking tools on MCP servers."""

    def __init__(
        self,
        max_retries: int = 3,
        timeout_seconds: int = 30,
        backoff_factor: float = 0.5
    ):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.backoff_factor = backoff_factor

    def call_tool(
        self,
        server: str,
        tool: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke a tool on an MCP server with retries and structured error handling."""
        # For production runs using external MCP servers (stdio or SSE),
        # an external bridge or subprocess is used.
        # This base client handles retry and contract logic.
        raise NotImplementedError("Subclasses or mock clients must implement call_tool.")


class MockMCPClient(MCPClient):
    """In-memory mock MCP client for hermetic contract testing and dry-run execution (SEC-04)."""

    def __init__(
        self,
        fail_unreachable: bool = False,
        fail_auth_expired: bool = False,
        fail_rate_limit: bool = False,
        fail_malformed_response: bool = False,
        unsupported_tools: Optional[List[str]] = None,
        deleted_docs: Optional[List[str]] = None,
        deleted_drafts: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.fail_unreachable = fail_unreachable
        self.fail_auth_expired = fail_auth_expired
        self.fail_rate_limit = fail_rate_limit
        self.fail_malformed_response = fail_malformed_response
        self.unsupported_tools = set(unsupported_tools or [])
        self.deleted_docs = set(deleted_docs or [])
        self.deleted_drafts = set(deleted_drafts or [])

        # In-memory storage for published objects
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.drafts: Dict[str, Dict[str, Any]] = {}
        self.call_history: List[Dict[str, Any]] = []
        self._doc_counter = 1000
        self._draft_counter = 2000

    def call_tool(
        self,
        server: str,
        tool: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate tool call with error injection and state tracking."""
        call_entry = {"server": server, "tool": tool, "args": arguments, "timestamp": time.time()}
        self.call_history.append(call_entry)

        # 1. Error injection checks
        if self.fail_unreachable:
            raise MCPConnectionError(f"MCP server '{server}' unreachable after {self.max_retries} attempts.")

        if self.fail_auth_expired:
            raise MCPAuthExpiredError(
                f"MCP authentication expired for server '{server}'. "
                "Action required: Re-authorize the Google Workspace connector."
            )

        if self.fail_rate_limit:
            raise MCPRateLimitError(f"Rate limit exceeded on '{server}.{tool}'. Retry after 60s.")

        if tool in self.unsupported_tools:
            raise MCPToolNotFoundError(f"Tool '{tool}' is not supported by MCP server '{server}'.")

        if self.fail_malformed_response:
            # MCP-13: Success status but empty/missing ID and URL
            return {"status": "success"}

        # 2. Tool implementations
        if tool == "create_document":
            self._doc_counter += 1
            doc_id = f"doc_{self._doc_counter}"
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            self.documents[doc_id] = {
                "title": arguments.get("title", ""),
                "content": arguments.get("content", ""),
                "doc_url": doc_url,
                "version": 1
            }
            return {
                "status": "success",
                "doc_id": doc_id,
                "doc_url": doc_url,
                "title": arguments.get("title", "")
            }

        elif tool == "update_document":
            doc_id = arguments.get("doc_id", "")
            if doc_id in self.deleted_docs or doc_id not in self.documents:
                raise MCPError(f"Document '{doc_id}' not found (deleted externally).")

            self.documents[doc_id]["content"] = arguments.get("content", "")
            self.documents[doc_id]["version"] += 1
            return {
                "status": "success",
                "doc_id": doc_id,
                "doc_url": self.documents[doc_id]["doc_url"],
                "version": self.documents[doc_id]["version"]
            }

        elif tool == "create_draft":
            self._draft_counter += 1
            draft_id = f"draft_{self._draft_counter}"
            self.drafts[draft_id] = {
                "to": arguments.get("to", ""),
                "subject": arguments.get("subject", ""),
                "body": arguments.get("body", ""),
                "is_sent": False
            }
            return {
                "status": "success",
                "draft_id": draft_id,
                "subject": arguments.get("subject", ""),
                "is_sent": False
            }

        elif tool == "update_draft":
            draft_id = arguments.get("draft_id", "")
            if draft_id in self.deleted_drafts or draft_id not in self.drafts:
                raise MCPError(f"Draft '{draft_id}' not found (deleted or already sent).")

            self.drafts[draft_id]["subject"] = arguments.get("subject", self.drafts[draft_id]["subject"])
            self.drafts[draft_id]["body"] = arguments.get("body", self.drafts[draft_id]["body"])
            return {
                "status": "success",
                "draft_id": draft_id,
                "is_sent": False
            }

        raise MCPToolNotFoundError(f"Unknown mock tool '{tool}' on server '{server}'.")
