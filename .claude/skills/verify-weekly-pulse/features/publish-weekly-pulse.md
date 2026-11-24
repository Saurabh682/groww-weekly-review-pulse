# Publish the weekly pulse

Turns a week of reviews into one validated note of at most 250 words, one Google Doc and one unsent Gmail draft. Running it again updates the same Doc and draft.

## Sub-features

- `pulse-dry-run` validates the note and contacts Google for nothing.
- `pulse-publish` creates one Doc and one draft.
- `pulse-noop` skips Google when the note is unchanged.
- `pulse-update` updates the same Doc and draft when the note changed.
- `pulse-files` leaves the note and a run report on disk.

## How to get to it (user POV)

- Run `python -m src.pipeline run --app <key> --week <date>` for the whole pipeline, with `--dry-run` to stop before publishing.
- Run `python -m src.pipeline publish --app <key> --week <date>` to publish from stored themes.
- A scheduled pulse job. See [Run scheduled jobs](./scheduled-jobs.md).

## Driving it with verify.py

Preconditions:

- Baseline state. No row in `publish_state`.

- **Dry run.** `python $V cli --run $RUN --name dry-run -- src.pipeline run --app groww --week 2026-11-09 --dry-run`. Exit 0, `status` is `validated`, `is_valid` true, `doc_url` null. Then `python $V composio --run $RUN --name after-dry-run` shows empty `documents`, `drafts` and `calls`.
- **Publish.** `python $V cli --run $RUN --name publish -- src.pipeline run --app groww --week 2026-11-09`. Exit 0, `status` is `published`, `word_count` is at most 250, `doc_url` and `draft_id` are set. Then `python $V composio --run $RUN --name after-publish` shows one document, one draft with `is_sent: false`, and exactly two calls: create document, create draft.
- **Unchanged rerun.** `python $V cli --run $RUN --name rerun -- src.pipeline publish --app groww --week 2026-11-09`. Prints `Publish status: NOOP`. Then `python $V composio --run $RUN --name after-rerun` shows the same two calls, no more.
- **Changed rerun.** Change the note by renaming the app: `python $V http --run $RUN --name rename --as operator --body '{"display_name":"Groww App"}' PATCH /apps/groww` gives 200. Then `python $V cli --run $RUN --name republish -- src.pipeline publish --app groww --week 2026-11-09` prints `PUBLISHED` with the same Doc and draft ids. `python $V composio --run $RUN --name after-republish` shows still one document and one draft, and only read and update calls after the first two.
- **Stored state.** `python $V db --run $RUN --name publish-state "select app_key, week_start, doc_id, draft_id from publish_state"` returns one row with the ids above.
- **Files.** `python $V keep --run $RUN --name note outputs/groww/2026-11-09/note.md` and `python $V keep --run $RUN --name run-report outputs/groww/2026-11-09/run_report.json`. The note is readable and the report is valid JSON.

## Gotchas

- Doc and draft ids come from the local stand-in (`doc0001`, `r0002`). The `docs.google.com` link is not a real document.
- The stand-in accepts any text. It does not prove how Google renders the note.
- A rename changes the draft's subject but not the existing Doc's title.
- `src.pipeline publish` needs stored themes, so run the pipeline once first.
