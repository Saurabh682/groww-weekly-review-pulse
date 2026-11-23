import json
import threading
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, urlsplit

from src.mcp.capabilities import MCPConfigData, load_mcp_config
from src.mcp.composio import ComposioClient, ComposioSettings

API_KEY = "composio-test-key"
DOCS_ACCOUNT = "ca_docs_test"
GMAIL_ACCOUNT = "ca_gmail_test"
NOT_FOUND = "Requested entity was not found."


@dataclass
class ToolCall:
    tool: str
    arguments: Dict[str, Any]
    account: Optional[str]


@dataclass
class FakeComposio:
    documents: Dict[str, Dict[str, str]] = field(default_factory=dict)
    drafts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    calls: List[ToolCall] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    sessions: Set[str] = field(default_factory=set)
    expired_accounts: Set[str] = field(default_factory=set)
    malformed_tools: Set[str] = field(default_factory=set)
    failing_tools: Set[str] = field(default_factory=set)
    http_failures: List[int] = field(default_factory=list)
    sse: bool = True
    _counter: int = 0

    def start(self) -> "FakeComposio":
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                return None

            def do_POST(self):
                fake.handle(self)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/v3/mcp/test-server?user_id=pulse-test"

    def settings(self, **accounts: str) -> ComposioSettings:
        pinned = {"googledocs": DOCS_ACCOUNT, "gmail": GMAIL_ACCOUNT}
        pinned.update(accounts)
        return ComposioSettings(url=self.url, api_key=API_KEY, accounts=pinned)

    def client(self, config: Optional[MCPConfigData] = None, **accounts: str) -> ComposioClient:
        return ComposioClient(self.settings(**accounts), config or fast_config())

    def tools_called(self) -> List[str]:
        return [c.tool for c in self.calls]

    def doc_text(self, doc_id: str) -> str:
        return self.documents[doc_id]["body"]

    def handle(self, request: BaseHTTPRequestHandler) -> None:
        if request.headers.get("x-api-key") != API_KEY:
            return self._reply(request, 401, {"error": "invalid api key"})
        if self.http_failures:
            return self._reply(request, self.http_failures.pop(0), {"error": "injected"})
        length = int(request.headers.get("Content-Length", "0"))
        message = json.loads(request.rfile.read(length).decode("utf-8"))
        method = message.get("method")
        self.methods.append(method)
        if method == "initialize":
            session = uuid.uuid4().hex
            self.sessions.add(session)
            return self._reply(request, 200, self._result(message, {
                "protocolVersion": message["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake-composio", "version": "1"},
            }), session=session)
        if request.headers.get("Mcp-Session-Id") not in self.sessions:
            return self._reply(request, 404, {"error": "unknown session"})
        if method == "notifications/initialized":
            return self._reply(request, 202, None)
        if method != "tools/call":
            return self._reply(request, 200, {"jsonrpc": "2.0", "id": message.get("id"),
                                              "error": {"code": -32601, "message": f"no method {method}"}})
        query = parse_qs(urlsplit(request.path).query)
        account = (query.get("connected_account_id") or [None])[0]
        name = message["params"]["name"]
        arguments = message["params"].get("arguments") or {}
        self.calls.append(ToolCall(name, arguments, account))
        envelope = self._run_tool(name, arguments, account)
        result = {"content": [{"type": "text", "text": json.dumps(envelope)}], "isError": not envelope["successful"]}
        return self._reply(request, 200, self._result(message, result))

    def _run_tool(self, name: str, args: Dict[str, Any], account: Optional[str]) -> Dict[str, Any]:
        if account in self.expired_accounts:
            return self._fail(f"Connected account {account} is EXPIRED. Please re-authenticate.")
        if name in self.failing_tools:
            return self._fail("Internal error from Google: backend unavailable")
        if name in self.malformed_tools:
            return {"successful": True, "data": {}, "error": None}
        handler = getattr(self, f"_tool_{name.lower()}", None)
        if handler is None:
            return self._fail(f"Tool {name} not found in this MCP server")
        return handler(args)

    def _tool_googledocs_create_document_markdown(self, args):
        doc_id = self._next("doc")
        self.documents[doc_id] = {"title": args["title"], "body": args.get("markdown_text", "")}
        return self._ok({"documentId": doc_id, "title": args["title"],
                         "display_url": f"https://docs.google.com/document/d/{doc_id}/edit"})

    def _tool_googledocs_get_document_by_id(self, args):
        doc = self.documents.get(args["id"])
        if doc is None:
            return self._fail(NOT_FOUND)
        end = len(doc["body"]) + 2
        return self._ok({"documentId": args["id"], "title": doc["title"],
                         "document_url": f"https://docs.google.com/document/d/{args['id']}/edit",
                         "body": {"content": [{"endIndex": 1, "sectionBreak": {}},
                                              {"startIndex": 1, "endIndex": end, "paragraph": {}}]}})

    def _tool_googledocs_update_existing_document(self, args):
        doc = self.documents.get(args["document_id"])
        if doc is None:
            return self._fail(NOT_FOUND)
        for edit in args["edit_docs"]:
            rng = edit["deleteContentRange"]["range"]
            start, end = rng["startIndex"], rng["endIndex"]
            if start < 1 or end > len(doc["body"]) + 1 or end <= start:
                return self._fail("Invalid requests[0].deleteContentRange: index out of range")
            doc["body"] = doc["body"][: start - 1] + doc["body"][end - 1:]
        return self._ok({"documentId": args["document_id"], "replies": [{}]})

    def _tool_googledocs_update_document_section_markdown(self, args):
        doc = self.documents.get(args["document_id"])
        if doc is None:
            return self._fail(NOT_FOUND)
        if "start_index" in args:
            return self._fail("fake supports append mode only")
        doc["body"] += args["markdown_text"]
        return self._ok({"documentId": args["document_id"]})

    def _tool_gmail_create_email_draft(self, args):
        draft_id = self._next("r")
        self.drafts[draft_id] = dict(args, is_sent=False)
        return self._ok({"id": draft_id, "message": {"id": self._next("m"), "labelIds": ["DRAFT"]}})

    def _tool_gmail_update_draft(self, args):
        if args["draft_id"] not in self.drafts:
            return self._fail(NOT_FOUND)
        self.drafts[args["draft_id"]].update({k: v for k, v in args.items() if k != "draft_id"})
        return self._ok({"id": args["draft_id"], "message": {"id": self._next("m"), "labelIds": ["DRAFT"]}})

    def _next(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}{self._counter:04d}"

    def _ok(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"successful": True, "data": data, "error": None}

    def _fail(self, error: str) -> Dict[str, Any]:
        return {"successful": False, "data": {}, "error": error}

    def _result(self, message: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": message["id"], "result": result}

    def _reply(self, request: BaseHTTPRequestHandler, status: int, payload, session: Optional[str] = None) -> None:
        if payload is None:
            body = b""
            content_type = "application/json"
        elif self.sse and status == 200:
            body = f"event: message\ndata: {json.dumps(payload)}\n\n".encode("utf-8")
            content_type = "text/event-stream"
        else:
            body = json.dumps(payload).encode("utf-8")
            content_type = "application/json"
        request.send_response(status)
        request.send_header("Content-Type", content_type)
        request.send_header("Content-Length", str(len(body)))
        if session:
            request.send_header("Mcp-Session-Id", session)
        request.end_headers()
        request.wfile.write(body)


def fast_config() -> MCPConfigData:
    config = load_mcp_config("config/mcp.yaml")
    policy = config.policy.model_copy(update={"backoff_seconds": 0, "timeout_seconds": 5})
    return config.model_copy(update={"policy": policy})
