---
name: verify-weekly-pulse
description: "Drive the real Weekly Review Pulse app (pipeline, registry and scheduler CLIs plus the HTTP API) in an isolated instance and capture proof. Use after changing anything in src/, config/, prompts/ or supabase/, before calling a change done, or when asked to verify, prove or demo pulse behavior."
---

# Verify Weekly Review Pulse

One helper, `scripts/verify.py`, starts an isolated copy of the app, drives it the way a user does, saves every step as evidence, and tears it down.

Run everything from the repository root, in Git Bash, with Python 3.13 and the project installed (`pip install ".[dev]"`). Set these once per shell:

```bash
export MSYS_NO_PATHCONV=1
V=.claude/skills/verify-weekly-pulse/scripts/verify.py
RUN=publish-fix-1
```

`RUN` is lowercase letters, digits and dashes. Use a new id every time. `MSYS_NO_PATHCONV=1` stops Git Bash from turning `/apps` into a Windows path.

## Surfaces

| Surface | Covered | How |
|---|---|---|
| Pipeline, registry and scheduler CLIs (`python -m src.pipeline`, `src.registry`, `src.scheduler`) | Yes | `verify.py cli` |
| HTTP API (`src.api.main:app`) | Yes | `verify.py http` |
| Web dashboard (`frontend/`) | **No** | Every page reads `frontend/src/data/mockApi.ts`. Driving it proves nothing about the app. Add it here when it calls the HTTP API. |
| GitHub Actions (`pulse.yml`) | **No** | Runs only from `main`. The scheduler commands it calls are covered. |
| Supabase and Postgres | **No** | Runs use SQLite. Set `PULSE_TEST_POSTGRES_DSN` to a throwaway local Postgres and run `python -m pytest`. |

## What is isolated and what is real

- **Data:** each run has its own `PULSE_HOME`. Nothing is written to `data/` or `outputs/`.
- **Settings:** the app gets an environment built from scratch. Every name found in `.env` or `.env.example` is set, so `.env` cannot supply a real value.
- **Publishing:** Composio is `tests/support/composio_server.py` on 127.0.0.1. It is the only stand-in. The app reaches it through its normal MCP client over HTTP.
- **Stores:** Google Play and the App Store are real and read-only. `registry search`, `registry add`, and `daily`, `reconcile` and `backfill` jobs need internet.
- **Parallel runs:** safe. Each run has its own ports, home and evidence.

## Launch

```bash
python $V launch --run $RUN
```

Ready means exit code 0 and `"ready": true`. By then the schema exists, Groww is registered, the API answers `/apps`, and `tests/fixtures/reviews_baseline.csv` is ingested for week `2026-11-09`.

## Doctor

```bash
python $V doctor --run $RUN
```

Read-only. Exit code 0 and `"healthy": true` means the instance is worth driving. Run it first when anything looks off.

| Failed check | Meaning |
|---|---|
| `server_is_ours`, `api_answers` | The server is gone or belongs to another run. Stop and launch a new id. |
| `operator_token_accepted` | Operator sign-in is broken. |
| `isolated_home`, `sqlite_store`, `supabase_unreachable`, `composio_is_local` | With the server up, isolation is broken: stop at once. |
| `build_unchanged` | Source changed after launch, so the API runs old code. Stop and launch a new id. |
| `user_data_untouched` | A file in `data/` or `outputs/` changed since launch. Find out what wrote it before trusting any proof. |

## Drive

| Step | Command |
|---|---|
| Run an app command | `python $V cli --run $RUN --name publish -- src.pipeline run --app groww --week 2026-11-09` |
| Give the scheduler its GitHub inputs | `python $V cli --run $RUN --name plan --env GITHUB_EVENT_NAME=schedule --env "PULSE_SCHEDULE=30 20 * * *" -- src.scheduler plan` |
| Call the API | `python $V http --run $RUN --name apps GET /apps` |
| Call it as a person | Add `--as operator`, `--as outsider` or `--as anonymous` (default), and `--body '<json>'` |
| See what reached Google | `python $V composio --run $RUN --name google` |
| Read stored rows | `python $V db --run $RUN --name state "select * from publish_state"` |
| Keep a produced file | `python $V keep --run $RUN --name note outputs/groww/2026-11-09/note.md` |

`cli` exits with the app's own exit code. `http` prints the status and exits 1 only for 5xx.

Use the recipes in [features/README.md](features/README.md). Drive every entry point the feature file lists.

## Evidence

Every step writes `runs/<run>/evidence/NNN-<name>.json` with the command or request, exit code or status, full output and time. `keep` copies a file next to them. The folder is git-ignored and survives `stop`.

- Drive the user's path: CLI or HTTP. `db`, `composio` and `keep` are for checking side effects, never for making them.
- Capture the action and the resulting state. For publishing, that is the command, then `composio`, then `publish_state`.
- `--dry-run` is proven by `composio` showing no calls, not by its name.
- A draft is proven unsent by `is_sent: false` and by no send tool in `calls`.
- Report a step you could not run, with the command and the unmet precondition. Never count it as verified through another path.
- After a live collection, select counts and statuses with `db`, not review text. Evidence must not hold real reviews.

## Cleanup

```bash
python $V stop --run $RUN
```

Stops only the server this run started, through its own control port. Removes the run's home and keeps the evidence, including `server.log`. Exit code 1 means `data/` or `outputs/` changed during the run. Run it after every failed attempt too.

Old evidence is deleted by hand: remove `runs/<run>`.

## Helpers

`scripts/verify.py` is the only helper. `python $V --help` and `python $V <action> --help` list its arguments. `serve` is internal: `launch` starts it.
