# Read pulses

Shows anyone the registered apps, an app's pulse history, one pulse with its themes and note, and how the last collection went.

## Sub-features

- `read-apps` lists apps.
- `read-history` lists weeks with themes, rating, Doc link and draft flag.
- `read-pulse` shows one week with its note.
- `read-health` shows the last collection per store and the latest pulse.
- `read-missing` gives a clear 404.

## How to get to it (user POV)

- `GET /apps`
- `GET /apps/{key}/pulses?limit=<n>`
- `GET /apps/{key}/pulses/{week}`
- `GET /apps/{key}/health`

## Driving it with verify.py

Preconditions:

- Baseline state, then `python $V cli --run $RUN --name publish -- src.pipeline run --app groww --week 2026-11-09`.

- **Apps.** `python $V http --run $RUN --name apps GET /apps` gives 200 with `groww`.
- **History.** `python $V http --run $RUN --name history GET /apps/groww/pulses` gives 200, one week with `status: published`, three themes, a Doc link and `draft_created: true`.
- **One pulse.** `python $V http --run $RUN --name pulse GET /apps/groww/pulses/2026-11-09` gives 200, `status: published`, window `2026-08-24` to `2026-11-15`, and `note_markdown` equal to the kept note.
- **Health.** `python $V http --run $RUN --name health GET /apps/groww/health` gives 200 and `latest_pulse.status` is `published`. `collections` holds nulls until a collection has run.
- **Missing app.** `python $V http --run $RUN --name missing-app GET /apps/nope/health` gives 404.
- **Missing week.** `python $V http --run $RUN --name missing-week GET /apps/groww/pulses/2020-01-06` gives 404.
- **Proof.** `python $V keep --run $RUN --name note outputs/groww/2026-11-09/note.md` matches `note_markdown`.

## Gotchas

- The API reads `note.md` from disk, so a week published by another machine has `note_markdown: null`.
