import json
import os
import time
import urllib.error
import urllib.parse
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


def account_endpoint(base_url: str, account_id: str) -> str:
    parts = urllib.parse.urlsplit(base_url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if k != "connected_account_id"]
    query.append(("connected_account_id", account_id))
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


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
        self._sessions: Dict[str, str] = {}
        self._request_id = 0

    @classmethod
    def from_env(cls, config: MCPConfigData, environ: Mapping[str, str] = os.environ) -> "ComposioClient":
        return cls(ComposioSettings.from_env(config, environ), config)

    def call(self, capability: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        target = resolve_capability(self.config, capability)
        account_id = (self.settings.accounts.get(target.toolkit) or "").strip()
        if not account_id:
            raise MCPAccountNotPinned(
                f"No connected-account ID for toolkit '{target.toolkit}' (CMP-02). "
                f"Set {self.config.accounts.get(target.toolkit, 'the account variable')}; nothing was called."
            )
        endpoint = account_endpoint(self.settings.url, account_id)
        result = self._call_with_retries(target, endpoint, arguments)
        return self._unwrap(target, result)

    def _call_with_retries(self, target: CapabilityTarget, endpoint: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        policy = self.config.policy
        last_error: Optional[BaseException] = None
        rate_limited = False
        for attempt in range(1, policy.max_retries + 1):
            try:
                session = self._session(target.toolkit, endpoint)
                return self._rpc(endpoint, session, "tools/call", {"name": target.tool, "arguments": arguments})
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    raise MCPAuthError(
                        f"Composio rejected the request with HTTP {exc.code}. "
                        f"Check {self.config.server.api_key_env} and {self.config.server.url_env}."
                    ) from exc
                if exc.code == 404 and target.toolkit in self._sessions:
                    self._sessions.pop(target.toolkit)
                    last_error = exc
                    continue
                if exc.code not in RETRYABLE_HTTP:
                    raise MCPError(f"Composio returned HTTP {exc.code} for {target.tool}.") from exc
                rate_limited = exc.code == 429
                last_error = exc
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                rate_limited = False
                last_error = exc
            if attempt < policy.max_retries:
                time.sleep(policy.backoff_seconds * (2 ** (attempt - 1)))
        error_type = MCPRateLimitError if rate_limited else MCPConnectionError
        raise error_type(
            f"Composio MCP unreachable after {policy.max_retries} attempts calling {target.tool}: {last_error}"
        )

    def _session(self, toolkit: str, endpoint: str) -> str:
        if toolkit in self._sessions:
            return self._sessions[toolkit]
        headers, _ = self._post(endpoint, "", self._message("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        }))
        session = headers.get(SESSION_HEADER) or ""
        self._post(endpoint, session, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        self._sessions[toolkit] = session
        return session

    def _rpc(self, endpoint: str, session: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._message(method, params)
        _, body = self._post(endpoint, session, payload)
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

    def _post(self, endpoint: str, session: str, payload: Dict[str, Any]) -> Tuple[Mapping[str, str], str]:
        headers = {
            "x-api-key": self.settings.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session:
            headers[SESSION_HEADER] = session
        request = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=self.config.policy.timeout_seconds) as response:
            return response.headers, response.read().decode("utf-8")

    def _unwrap(self, target: CapabilityTarget, result: Dict[str, Any]) -> Dict[str, Any]:
        envelope, text = tool_envelope(result)
        failed = bool(result.get("isError")) or (envelope is not None and envelope.get("successful") is False)
        if failed:
            detail = (envelope or {}).get("error") or text or "no error detail"
            raise self._classify(target, str(detail))
        data = (envelope or {}).get("data")
        if not isinstance(data, dict):
            raise MCPMalformedResponse(f"{target.tool} returned success without a data object (MCP-13).")
        return data

    def _classify(self, target: CapabilityTarget, detail: str) -> MCPError:
        snippet = detail[:ERROR_TEXT_LIMIT]
        lowered = snippet.lower()
        if any(marker in lowered for marker in EXPIRED_MARKERS):
            label = TOOLKIT_LABELS.get(target.toolkit, target.toolkit)
            return MCPConnectionExpired(
                f"Reconnect {label} in Composio: the account in {self.config.accounts[target.toolkit]} "
                f"is no longer usable (CMP-07). The local Markdown note is kept. Detail: {snippet}"
            )
        if any(marker in lowered for marker in NOT_FOUND_MARKERS):
            return MCPNotFoundError(f"{target.tool}: {snippet}")
        return MCPError(f"{target.tool} failed: {snippet}")
