import http.client
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Tuple

from src.mcp.capabilities import CapabilityTarget, MCPConfigData, resolve_capability
from src.mcp.errors import (
    MCPAccountNotPinned,
    MCPAuthError,
    MCPConnectionError,
    MCPConnectionExpired,
    MCPError,
    MCPMalformedResponse,
    MCPMissingSetting,
    MCPNotFoundError,
    MCPRateLimitError,
    MCPToolNotFoundError,
)

PROTOCOL_VERSION = "2025-03-26"
CLIENT_INFO = {"name": "weekly-review-pulse", "version": "2.0.0"}
SESSION_HEADER = "Mcp-Session-Id"
EXECUTE_TOOL = "COMPOSIO_MULTI_EXECUTE_TOOL"
CONNECTIONS_TOOL = "COMPOSIO_MANAGE_CONNECTIONS"
REPLAY_UNSAFE_CAPABILITIES = ("docs.create", "docs.clear", "docs.write", "gmail.create_draft")
RETRYABLE_HTTP = (429, 500, 502, 503, 504)
EXPIRED_MARKERS = (
    "expired",
    "invalid_grant",
    "not active",
    "inactive",
    "re-auth",
    "reauth",
    "reconnect",
    "invalid authentication credentials",
    "unauthenticated",
    "no connected account",
    "connected account not found",
)
NOT_FOUND_MARKERS = ("not found", "404", "not a draft")
TOOLKIT_LABELS = {"googledocs": "Google Docs", "gmail": "Gmail"}
ERROR_TEXT_LIMIT = 300


class ToolCaller(Protocol):
    def verify_accounts(self) -> None: ...

    def call(self, capability: str, arguments: Dict[str, Any]) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class ComposioSettings:
    url: str
    api_key: str
    accounts: Dict[str, str]

    @classmethod
    def from_env(cls, config: MCPConfigData, environ: Mapping[str, str] = os.environ) -> "ComposioSettings":
        names = [config.server.url_env, config.server.api_key_env, *config.accounts.values()]
        missing = [name for name in names if not environ.get(name, "").strip()]
        if missing:
            raise MCPMissingSetting(
                f"Composio publishing needs these environment variables: {', '.join(missing)} (CMP-10). "
                "Set them in .env or the job secrets."
            )
        return cls(
            url=environ[config.server.url_env].strip(),
            api_key=environ[config.server.api_key_env].strip(),
            accounts={toolkit: environ[env].strip() for toolkit, env in config.accounts.items()},
        )


def decode_rpc_body(body: str, request_id: int) -> Dict[str, Any]:
    stripped = body.strip()
    if stripped.startswith("{"):
        candidates = [stripped]
    else:
        candidates = [line[5:].strip() for line in body.splitlines() if line.startswith("data:")]
    for candidate in candidates:
        try:
            message = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(message, dict) and message.get("id") == request_id:
            return message
    raise MCPMalformedResponse(f"Composio MCP reply had no JSON-RPC response for request {request_id}.")


def tool_envelope(result: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], str]:
    texts = [c.get("text", "") for c in result.get("content") or [] if isinstance(c, dict) and c.get("type") == "text"]
    text = "\n".join(t for t in texts if t)
    structured = result.get("structuredContent")
    if isinstance(structured, dict) and ("successful" in structured or "data" in structured):
        return structured, text
    for candidate in texts:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed, text
    return None, text


class ComposioClient:
    def __init__(self, settings: ComposioSettings, config: MCPConfigData):
        self.settings = settings
        self.config = config
        self._session_id: Optional[str] = None
        self._verified: Dict[str, str] = {}
        self._request_id = 0

    @classmethod
    def from_env(cls, config: MCPConfigData, environ: Mapping[str, str] = os.environ) -> "ComposioClient":
        return cls(ComposioSettings.from_env(config, environ), config)

    def call(self, capability: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        target = resolve_capability(self.config, capability)
        self._pinned_account(target.toolkit)
        self.verify_accounts()
        item = {"tool_slug": target.tool, "arguments": arguments, "account": self._verified[target.toolkit]}
        result = self._call_meta_tool(
            EXECUTE_TOOL,
            {"tools": [item], "sync_response_to_workbench": False},
            target.tool,
            replay_safe=capability not in REPLAY_UNSAFE_CAPABILITIES,
        )
        return self._unwrap(target, result)

    def verify_accounts(self) -> None:
        if self._verified:
            return
        pins = {toolkit: self._pinned_account(toolkit) for toolkit in self.config.accounts}
        listing = [{"name": toolkit, "action": "list"} for toolkit in pins]
        result = self._call_meta_tool(CONNECTIONS_TOOL, {"toolkits": listing}, CONNECTIONS_TOOL, replay_safe=True)
        envelope, text = tool_envelope(result)
        data = (envelope or {}).get("data")
        connections = data.get("results") if isinstance(data, dict) else None
        if result.get("isError") or not isinstance(connections, dict):
            raise MCPMalformedResponse(f"Composio did not list connected accounts: {text[:ERROR_TEXT_LIMIT]}")
        self._verified = {toolkit: self._match_account(toolkit, pin, connections) for toolkit, pin in pins.items()}

    def _pinned_account(self, toolkit: str) -> str:
        account = (self.settings.accounts.get(toolkit) or "").strip()
        if not account:
            raise MCPAccountNotPinned(
                f"No connected account for toolkit '{toolkit}' (CMP-02). "
                f"Set {self.config.accounts[toolkit]}; nothing was called."
            )
        return account

    def _match_account(self, toolkit: str, pin: str, connections: Dict[str, Any]) -> str:
        accounts = (connections.get(toolkit) or {}).get("accounts") or []
        matches = [a for a in accounts if pin in (a.get("id"), a.get("alias"))]
        variable = self.config.accounts[toolkit]
        if len(matches) != 1:
            known = ", ".join(str(a.get("id")) for a in accounts) or "none"
            raise MCPAccountNotPinned(
                f"{variable} matches {len(matches)} {TOOLKIT_LABELS.get(toolkit, toolkit)} accounts (CMP-02). "
                f"Connected account IDs: {known}. Nothing was published."
            )
        status = str(matches[0].get("status", "")).lower()
        if status != "active":
            raise self._expired(toolkit, f"status is {status or 'unknown'}")
        return str(matches[0]["id"])

    def _call_meta_tool(self, name: str, arguments: Dict[str, Any], label: str, replay_safe: bool) -> Dict[str, Any]:
        policy = self.config.policy
        last_error: Optional[BaseException] = None
        rate_limited = False
        for attempt in range(1, policy.max_retries + 1):
            request_sent = False
            try:
                session = self._session()
                request_sent = True
                return self._rpc(session, "tools/call", {"name": name, "arguments": arguments})
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    raise MCPAuthError(
                        f"Composio rejected the request with HTTP {exc.code}. "
                        f"Check {self.config.server.api_key_env} and {self.config.server.url_env}."
                    ) from exc
                session_lost = exc.code == 404 and bool(self._session_id)
                if session_lost:
                    self._session_id = None
                elif exc.code not in RETRYABLE_HTTP:
                    raise MCPError(f"Composio returned HTTP {exc.code} for {label}.") from exc
                rate_limited = exc.code == 429
                never_executed = session_lost or rate_limited or not request_sent
                last_error = exc
            except (OSError, http.client.HTTPException) as exc:
                rate_limited = False
                never_executed = not request_sent
                last_error = exc
            if not (replay_safe or never_executed):
                raise MCPConnectionError(
                    f"{label} may have completed, so it was not retried (MCP-23): {last_error}"
                ) from last_error
            if attempt < policy.max_retries:
                time.sleep(policy.backoff_seconds * (2 ** (attempt - 1)))
        error_type = MCPRateLimitError if rate_limited else MCPConnectionError
        raise error_type(f"Composio MCP unreachable after {policy.max_retries} attempts calling {label}: {last_error}")

    def _session(self) -> str:
        if self._session_id is not None:
            return self._session_id
        headers, _ = self._post("", self._message("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        }))
        session = headers.get(SESSION_HEADER) or ""
        self._post(session, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        self._session_id = session
        return session

    def _rpc(self, session: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._message(method, params)
        _, body = self._post(session, payload)
        message = decode_rpc_body(body, payload["id"])
        if "error" in message:
            error = message["error"] or {}
            if error.get("code") == -32601:
                raise MCPToolNotFoundError(f"Composio MCP does not offer {params.get('name')}: {error.get('message')}")
            raise MCPError(f"Composio MCP error {error.get('code')}: {error.get('message')}")
        result = message.get("result")
        if not isinstance(result, dict):
            raise MCPMalformedResponse("Composio MCP returned a response with no result object.")
        return result

    def _message(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._request_id += 1
        return {"jsonrpc": "2.0", "id": self._request_id, "method": method, "params": params}

    def _post(self, session: str, payload: Dict[str, Any]) -> Tuple[Mapping[str, str], str]:
        headers = {
            self.config.server.api_key_header: self.settings.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session:
            headers[SESSION_HEADER] = session
        request = urllib.request.Request(
            self.settings.url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=self.config.policy.timeout_seconds) as response:
            return response.headers, response.read().decode("utf-8")

    def _unwrap(self, target: CapabilityTarget, result: Dict[str, Any]) -> Dict[str, Any]:
        envelope, text = tool_envelope(result)
        envelope = envelope or {}
        outer = envelope.get("data")
        results = outer.get("results") if isinstance(outer, dict) else None
        item = results[0] if isinstance(results, list) and results and isinstance(results[0], dict) else {}
        if not item:
            if result.get("isError") or envelope.get("error") or envelope.get("successful") is False:
                raise self._classify(target, str(envelope.get("error") or text or "no error detail"))
            raise MCPMalformedResponse(f"{target.tool} returned no result (MCP-13).")
        response = item.get("response")
        response = response if isinstance(response, dict) else {}
        error = response.get("error") or item.get("error")
        if error or result.get("isError") or response.get("successful") is False:
            raise self._classify(target, str(error or "no error detail"))
        data = response.get("data")
        if not isinstance(data, dict):
            raise MCPMalformedResponse(f"{target.tool} returned success without a data object (MCP-13).")
        return data

    def _expired(self, toolkit: str, detail: str) -> MCPConnectionExpired:
        return MCPConnectionExpired(
            f"Reconnect {TOOLKIT_LABELS.get(toolkit, toolkit)} in Composio: the account in "
            f"{self.config.accounts[toolkit]} is no longer usable (CMP-07). "
            f"The local Markdown note is kept. Detail: {detail}"
        )

    def _classify(self, target: CapabilityTarget, detail: str) -> MCPError:
        snippet = detail[:ERROR_TEXT_LIMIT]
        lowered = snippet.lower()
        if any(marker in lowered for marker in EXPIRED_MARKERS):
            return self._expired(target.toolkit, snippet)
        if any(marker in lowered for marker in NOT_FOUND_MARKERS):
            return MCPNotFoundError(f"{target.tool}: {snippet}")
        return MCPError(f"{target.tool} failed: {snippet}")
