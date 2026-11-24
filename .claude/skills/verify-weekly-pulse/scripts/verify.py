import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[4]
RUNS = Path(__file__).resolve().parents[1] / "runs"
SEED_WEEK = "2026-11-09"
SEED_FILE = "tests/fixtures/reviews_baseline.csv"
OPERATOR = "operator@example.com"
OUTSIDER = "outsider@example.com"
RECIPIENT = "verify@example.com"
READY_SECONDS = 120
CLI_SECONDS = 900
RUN_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
ENV_NAME = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=", re.MULTILINE)
CLI_MODULES = ("src.pipeline", "src.registry", "src.scheduler")
BUILD_PATHS = ("src", "config", "prompts", "tests/support", "supabase")
HOST_ENV = (
    "PATH", "SYSTEMROOT", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR", "HOME",
    "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "LANG", "LC_ALL",
)


class VerifyError(Exception):
    pass


def run_dir(run_id: str) -> Path:
    if not RUN_ID.fullmatch(run_id):
        raise VerifyError("Run id must be lowercase letters, digits and dashes.")
    return RUNS / run_id


def home_dir(run_id: str) -> Path:
    return run_dir(run_id) / "home"


def evidence_dir(run_id: str) -> Path:
    return run_dir(run_id) / "evidence"


def state_path(run_id: str) -> Path:
    return run_dir(run_id) / "state.json"


def load_state(run_id: str) -> Dict[str, Any]:
    if not state_path(run_id).is_file():
        raise VerifyError(f"Run {run_id!r} is not launched. Start it with: launch --run {run_id}")
    return json.loads(state_path(run_id).read_text(encoding="utf-8"))


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def blocked_names() -> List[str]:
    names = set()
    for name in (".env", ".env.example"):
        path = ROOT / name
        if path.is_file():
            names.update(ENV_NAME.findall(path.read_text(encoding="utf-8")))
    return sorted(names)


def base_env(run_id: str, jwt_secret: str) -> Dict[str, str]:
    env = {name: os.environ[name] for name in HOST_ENV if name in os.environ}
    env.update({name: "" for name in blocked_names()})
    env.update({
        "PYTHONUTF8": "1",
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": str(ROOT),
        "PULSE_HOME": str(home_dir(run_id)),
        "PULSE_STORE": "sqlite",
        "PULSE_EMAIL_TO": RECIPIENT,
        "SUPABASE_DB_URL": "",
        "SUPABASE_URL": "",
        "SUPABASE_JWT_SECRET": jwt_secret,
        "OPERATOR_EMAILS": OPERATOR,
        "GITHUB_REPOSITORY": "",
        "GITHUB_DISPATCH_TOKEN": "",
        "CORS_ORIGINS": "",
        "COMPOSIO_MCP_URL": "",
        "COMPOSIO_API_KEY": "",
        "COMPOSIO_GOOGLEDOCS_ACCOUNT_ID": "",
        "COMPOSIO_GMAIL_ACCOUNT_ID": "",
    })
    return env


def composio_env(url: str) -> Dict[str, str]:
    sys.path.insert(0, str(ROOT))
    from tests.support.composio_server import API_KEY, DOCS_ACCOUNT, GMAIL_ACCOUNT

    return {
        "COMPOSIO_MCP_URL": url,
        "COMPOSIO_API_KEY": API_KEY,
        "COMPOSIO_GOOGLEDOCS_ACCOUNT_ID": DOCS_ACCOUNT,
        "COMPOSIO_GMAIL_ACCOUNT_ID": GMAIL_ACCOUNT,
    }


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def build_stamp() -> Dict[str, str]:
    digest = hashlib.sha256()
    for name in BUILD_PATHS:
        for path in sorted((ROOT / name).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
                digest.update(path.read_bytes())
    return {"commit": git("rev-parse", "--short", "HEAD"), "source": digest.hexdigest()[:16]}


def user_data_stamp() -> Dict[str, List[int]]:
    files = (p for name in ("data", "outputs") for p in (ROOT / name).rglob("*") if p.is_file())
    return {p.relative_to(ROOT).as_posix(): [p.stat().st_mtime_ns, p.stat().st_size] for p in files}


def call(method: str, url: str, body: Optional[str] = None, headers: Optional[Dict[str, str]] = None,
         timeout: int = 60) -> Tuple[int, str]:
    data = body.encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def control(state: Dict[str, Any], method: str, path: str) -> Dict[str, Any]:
    status, body = call(method, f"{state['control_url']}{path}", headers={"X-Verify-Token": state["token"]}, timeout=10)
    if status != 200:
        raise VerifyError(f"Control server returned HTTP {status} for {path}.")
    return json.loads(body)


def save_evidence(run_id: str, name: str, record: Dict[str, Any]) -> Path:
    folder = evidence_dir(run_id)
    folder.mkdir(parents=True, exist_ok=True)
    taken = [int(p.name[:3]) for p in folder.glob("[0-9][0-9][0-9]-*.json")]
    number = max(taken, default=0) + 1
    path = folder / f"{number:03d}-{name}.json"
    record = {"run": run_id, "recorded_at": datetime.now(timezone.utc).isoformat(), **record}
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def operator_token(state: Dict[str, Any], email: str) -> str:
    import jwt

    claims = {"sub": "verify", "aud": "authenticated", "email": email,
              "exp": datetime.now(timezone.utc) + timedelta(minutes=10)}
    return jwt.encode(claims, state["jwt_secret"], algorithm="HS256")


def serve(run_id: str) -> int:
    import uvicorn

    state = load_state(run_id)
    sys.path.insert(0, str(ROOT))
    from tests.support.composio_server import FakeComposio

    fake = FakeComposio().start()
    api_server = uvicorn.Server(uvicorn.Config("src.api.main:app", host="127.0.0.1", port=state["api_port"],
                                               log_level="info"))

    class Control(BaseHTTPRequestHandler):
        def log_message(self, *args):
            return None

        def _send(self, status: int, payload: Dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _allowed(self) -> bool:
            if secrets.compare_digest(self.headers.get("X-Verify-Token", ""), state["token"]):
                return True
            self._send(403, {"error": "wrong token"})
            return False

        def do_GET(self):
            if not self._allowed():
                return
            if self.path == "/health":
                self._send(200, {"run": run_id, "home": os.environ["PULSE_HOME"], "store": os.environ["PULSE_STORE"],
                                 "supabase_configured": bool(os.environ["SUPABASE_DB_URL"]),
                                 "composio_url": fake.url, "api_ready": api_server.started})
            elif self.path == "/composio":
                self._send(200, {"documents": fake.documents, "drafts": fake.drafts,
                                 "calls": [asdict(c) for c in fake.calls]})
            else:
                self._send(404, {"error": "unknown path"})

        def do_POST(self):
            if not self._allowed():
                return
            if self.path != "/stop":
                self._send(404, {"error": "unknown path"})
                return
            self._send(200, {"stopping": True})
            api_server.should_exit = True

    control_server = ThreadingHTTPServer(("127.0.0.1", state["control_port"]), Control)
    threading.Thread(target=control_server.serve_forever, daemon=True).start()
    api_server.run()
    control_server.shutdown()
    control_server.server_close()
    fake.stop()
    return 0


def wait_ready(run_id: str, process: subprocess.Popen) -> Dict[str, Any]:
    state = load_state(run_id)
    deadline = time.monotonic() + READY_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise VerifyError(f"Server exited with code {process.returncode}. See {run_dir(run_id) / 'server.log'}")
        try:
            health = control(state, "GET", "/health")
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            health = {}
        if health.get("api_ready") and call("GET", f"{state['api_url']}/apps")[0] == 200:
            return health
        time.sleep(0.2)
    raise VerifyError(f"Server was not ready in {READY_SECONDS}s. See {run_dir(run_id) / 'server.log'}")


def run_module(run_id: str, module: str, args: List[str], extra_env: Dict[str, str]) -> subprocess.CompletedProcess:
    state = load_state(run_id)
    env = {**base_env(run_id, state["jwt_secret"]), **composio_env(state["composio_url"]), **extra_env}
    return subprocess.run([sys.executable, "-m", module, *args], cwd=ROOT, env=env, capture_output=True, text=True,
                          encoding="utf-8", stdin=subprocess.DEVNULL, timeout=CLI_SECONDS)


def launch(run_id: str) -> int:
    folder = run_dir(run_id)
    if state_path(run_id).exists():
        raise VerifyError(f"Run {run_id!r} is already launched. Use another id, or: stop --run {run_id}")
    if evidence_dir(run_id).exists():
        raise VerifyError(f"Run {run_id!r} already has evidence. Use a new id.")
    home_dir(run_id).mkdir(parents=True)
    api_port, control_port = free_port(), free_port()
    state = {
        "run": run_id,
        "token": secrets.token_urlsafe(24),
        "jwt_secret": secrets.token_urlsafe(48),
        "api_port": api_port,
        "api_url": f"http://127.0.0.1:{api_port}",
        "control_port": control_port,
        "control_url": f"http://127.0.0.1:{control_port}",
        "composio_url": "",
        "build": build_stamp(),
        "user_data": user_data_stamp(),
    }
    state_path(run_id).write_text(json.dumps(state), encoding="utf-8")
    detach = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS}
              if os.name == "nt" else {"start_new_session": True})
    with open(folder / "server.log", "w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "serve", "--run", run_id], cwd=ROOT,
                                   env=base_env(run_id, state["jwt_secret"]), stdin=subprocess.DEVNULL, stdout=log,
                                   stderr=subprocess.STDOUT, **detach)
    state["pid"] = process.pid
    state_path(run_id).write_text(json.dumps(state), encoding="utf-8")
    health = wait_ready(run_id, process)
    state["composio_url"] = health["composio_url"]
    state_path(run_id).write_text(json.dumps(state), encoding="utf-8")
    seeded = run_module(run_id, "src.pipeline",
                        ["ingest", "--app", "groww", "--week", SEED_WEEK, "--file", SEED_FILE], {})
    path = save_evidence(run_id, "seed", {"exit_code": seeded.returncode, "stdout": seeded.stdout,
                                         "stderr": seeded.stderr})
    if seeded.returncode != 0:
        raise VerifyError(f"Seeding failed. See {path}")
    print(json.dumps({"run": run_id, "ready": True, "api_url": state["api_url"], "seed_week": SEED_WEEK,
                      "evidence": str(evidence_dir(run_id))}, indent=2))
    return 0


def doctor(run_id: str) -> int:
    state = load_state(run_id)
    checks: Dict[str, bool] = {}
    try:
        health = control(state, "GET", "/health")
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        health = {}
    checks["server_is_ours"] = health.get("run") == run_id
    checks["api_answers"] = bool(health) and call("GET", f"{state['api_url']}/apps")[0] == 200
    checks["operator_token_accepted"] = bool(health) and call(
        "PATCH", f"{state['api_url']}/apps/no-such-app", '{"display_name": "Probe"}',
        {"Authorization": f"Bearer {operator_token(state, OPERATOR)}"})[0] == 404
    checks["isolated_home"] = health.get("home") == str(home_dir(run_id))
    checks["sqlite_store"] = health.get("store") == "sqlite"
    checks["supabase_unreachable"] = health.get("supabase_configured") is False
    checks["composio_is_local"] = str(health.get("composio_url", "")).startswith("http://127.0.0.1:")
    checks["build_unchanged"] = build_stamp() == state["build"]
    checks["user_data_untouched"] = user_data_stamp() == state["user_data"]
    healthy = all(checks.values())
    print(json.dumps({"run": run_id, "healthy": healthy, "build": state["build"], "checks": checks}, indent=2))
    return 0 if healthy else 1


def cli(run_id: str, name: str, env_pairs: List[str], command: List[str]) -> int:
    command = command[1:] if command[:1] == ["--"] else command
    if not command or command[0] not in CLI_MODULES:
        raise VerifyError(f"The command must start with one of {CLI_MODULES}.")
    extra = dict(pair.split("=", 1) for pair in env_pairs)
    refused = sorted(k for k in extra if k not in ("GITHUB_EVENT_NAME", "PULSE_SCHEDULE", "PULSE_MODE", "PULSE_APP_KEY"))
    if refused:
        raise VerifyError(f"--env accepts only the scheduler inputs, not {refused}.")
    output_file = run_dir(run_id) / "home" / "github_output.txt"
    output_file.unlink(missing_ok=True)
    result = run_module(run_id, command[0], command[1:], {**extra, "GITHUB_OUTPUT": str(output_file)})
    github_output = output_file.read_text(encoding="utf-8") if output_file.exists() else None
    path = save_evidence(run_id, name, {"command": ["python", "-m", *command], "env": extra,
                                       "exit_code": result.returncode, "stdout": result.stdout,
                                       "stderr": result.stderr, "github_output": github_output})
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    print(f"[exit {result.returncode}] evidence: {path}")
    return result.returncode


def http(run_id: str, name: str, method: str, path: str, body: Optional[str], caller: str) -> int:
    state = load_state(run_id)
    email = {"operator": OPERATOR, "outsider": OUTSIDER}.get(caller)
    headers = {"Authorization": f"Bearer {operator_token(state, email)}"} if email else {}
    status, text = call(method, f"{state['api_url']}{path}", body, headers)
    saved = save_evidence(run_id, name, {"request": {"method": method, "path": path, "body": body, "caller": caller},
                                        "status": status, "response": text})
    print(text)
    print(f"[http {status}] evidence: {saved}")
    return 0 if status < 500 else 1


def composio(run_id: str, name: str) -> int:
    record = control(load_state(run_id), "GET", "/composio")
    saved = save_evidence(run_id, name, {"composio": record})
    print(json.dumps({
        "documents": {k: {"title": v["title"], "characters": len(v["body"])} for k, v in record["documents"].items()},
        "drafts": {k: {"subject": v.get("subject"), "is_sent": v["is_sent"]} for k, v in record["drafts"].items()},
        "calls": [c["tool"] for c in record["calls"]],
    }, indent=2, ensure_ascii=False))
    print(f"evidence: {saved}")
    return 0


def db(run_id: str, name: str, query: str) -> int:
    load_state(run_id)
    database = home_dir(run_id) / "data" / "pulse.db"
    conn = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(query)]
    finally:
        conn.close()
    saved = save_evidence(run_id, name, {"query": query, "rows": rows})
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"evidence: {saved}")
    return 0


def keep(run_id: str, name: str, relative: str) -> int:
    load_state(run_id)
    source = (home_dir(run_id) / relative).resolve()
    if not source.is_relative_to(home_dir(run_id).resolve()) or not source.is_file():
        raise VerifyError(f"{relative!r} is not a file in this run's home.")
    target = evidence_dir(run_id) / f"{name}{source.suffix}"
    if target.exists():
        raise VerifyError(f"{target.name} already exists in the evidence folder.")
    shutil.copy2(source, target)
    print(f"evidence: {target}")
    return 0


def port_open(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def remove_home(run_id: str) -> None:
    home = home_dir(run_id)
    deadline = time.monotonic() + 15
    while home.exists():
        try:
            shutil.rmtree(home)
        except PermissionError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.2)


def stop(run_id: str) -> int:
    state = load_state(run_id)
    untouched = user_data_stamp() == state["user_data"]
    try:
        control(state, "POST", "/stop")
        answered = True
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        answered = False
    deadline = time.monotonic() + 20
    while answered and time.monotonic() < deadline and (port_open(state["api_port"]) or port_open(state["control_port"])):
        time.sleep(0.2)
    if answered and (port_open(state["api_port"]) or port_open(state["control_port"])):
        raise VerifyError(f"Server pid {state['pid']} did not stop. Nothing was removed.")
    remove_home(run_id)
    log = run_dir(run_id) / "server.log"
    if log.exists():
        evidence_dir(run_id).mkdir(parents=True, exist_ok=True)
        shutil.move(str(log), str(evidence_dir(run_id) / "server.log"))
    state_path(run_id).unlink()
    print(json.dumps({"run": run_id, "server_stopped": answered, "user_data_untouched": untouched,
                      "home_removed": not home_dir(run_id).exists(),
                      "evidence": sorted(p.name for p in evidence_dir(run_id).iterdir())}, indent=2))
    return 0 if untouched else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verify.py", description="Drive an isolated Weekly Review Pulse")
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("launch", "serve", "doctor", "stop"):
        sub.add_parser(action).add_argument("--run", required=True)
    for action in ("cli", "http", "composio", "db", "keep"):
        step = sub.add_parser(action)
        step.add_argument("--run", required=True)
        step.add_argument("--name", required=True, help="Evidence name, lowercase with dashes")
        if action == "cli":
            step.add_argument("--env", action="append", default=[], metavar="NAME=VALUE")
            step.add_argument("command", nargs=argparse.REMAINDER)
        if action == "http":
            step.add_argument("--as", dest="caller", choices=("anonymous", "outsider", "operator"), default="anonymous")
            step.add_argument("--body", default=None)
            step.add_argument("method", choices=("GET", "POST", "PATCH", "DELETE"))
            step.add_argument("path")
        if action == "db":
            step.add_argument("query")
        if action == "keep":
            step.add_argument("path", help="File inside the run's home")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if hasattr(args, "name") and not RUN_ID.fullmatch(args.name):
        raise VerifyError("Evidence name must be lowercase letters, digits and dashes.")
    if args.action == "launch":
        return launch(args.run)
    if args.action == "serve":
        return serve(args.run)
    if args.action == "doctor":
        return doctor(args.run)
    if args.action == "stop":
        return stop(args.run)
    if args.action == "cli":
        return cli(args.run, args.name, args.env, args.command)
    if args.action == "http":
        return http(args.run, args.name, args.method, args.path, args.body, args.caller)
    if args.action == "composio":
        return composio(args.run, args.name)
    if args.action == "db":
        return db(args.run, args.name, args.query)
    return keep(args.run, args.name, args.path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        sys.exit(main())
    except VerifyError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(2)
