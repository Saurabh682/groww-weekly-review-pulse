import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, Tuple

DISPATCH_URL = "https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
WORKFLOW_FILE = "pulse.yml"
DEFAULT_REF = "main"

HttpPost = Callable[[str, bytes, dict], Tuple[int, bytes]]


@dataclass
class DispatchResult:
    status: str
    detail: Optional[str] = None


class BackfillDispatcher(Protocol):
    def dispatch_backfill(self, app_key: str) -> DispatchResult:
        ...


def urllib_post(url: str, body: bytes, headers: dict) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, b""


class GitHubDispatcher:
    def __init__(self, repo: str, token: str, ref: str = DEFAULT_REF, http_post: HttpPost = urllib_post):
        self._url = DISPATCH_URL.format(repo=repo, workflow=WORKFLOW_FILE)
        self._token = token
        self._ref = ref
        self._http_post = http_post

    def dispatch_backfill(self, app_key: str) -> DispatchResult:
        body = json.dumps({"ref": self._ref, "inputs": {"mode": "backfill", "app_key": app_key}}).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        }
        try:
            status, _ = self._http_post(self._url, body, headers)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            return DispatchResult("failed", f"GitHub unreachable: {type(exc).__name__}")
        if status == 204:
            return DispatchResult("dispatched")
        return DispatchResult("failed", f"GitHub returned HTTP {status}")


class UnconfiguredDispatcher:
    def dispatch_backfill(self, app_key: str) -> DispatchResult:
        return DispatchResult("not_configured", "Set GITHUB_REPOSITORY and GITHUB_DISPATCH_TOKEN to start backfills.")


def dispatcher_from_env() -> BackfillDispatcher:
    repo = os.getenv("GITHUB_REPOSITORY", "").strip()
    token = os.getenv("GITHUB_DISPATCH_TOKEN", "").strip()
    if repo and token:
        return GitHubDispatcher(repo, token, ref=os.getenv("GITHUB_DISPATCH_REF", DEFAULT_REF))
    return UnconfiguredDispatcher()
