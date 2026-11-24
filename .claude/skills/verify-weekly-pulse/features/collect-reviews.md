# Collect reviews

Fetches recent reviews for an app from Google Play and the App Store, removes personal details and duplicates, and stores them.

## Sub-features

- `collect-daily` fetches the last days from both stores.
- `collect-dedupe` never stores the same review twice.
- `collect-record` records each store's result separately.

## How to get to it (user POV)

- Run `python -m src.pipeline collect --app <key> --mode daily`.
- The scheduled daily job: `python -m src.scheduler run --app <key> --mode daily`.

## Driving it with verify.py

Preconditions:

- Baseline state.
- Internet, and both stores answering.

- **Scheduled entry.** `python $V cli --run $RUN --name daily -- src.scheduler run --app groww --mode daily`. Exit 0, `status` is `ok`, both platforms `ok`, and `inserted` is at most `fetched`.
- **CLI entry, second run.** `python $V cli --run $RUN --name daily-again -- src.pipeline collect --app groww --mode daily`. Exit 0 and both platforms `ok`.
- **No duplicates.** `python $V db --run $RUN --name duplicates "select count(*) as duplicate_groups from (select platform, date, rating, text from reviews group by 1, 2, 3, 4 having count(*) > 1)"`. `duplicate_groups` is 0.
- **Records.** `python $V db --run $RUN --name collections "select platform, mode, status, fetched, inserted, window_start, window_end from collection_runs order by collection_id"`. One row per store per run.
- **Health view.** `python $V http --run $RUN --name health GET /apps/groww/health` shows the latest collection for both stores.
- **Proof.** `python $V db --run $RUN --name counts "select platform, count(*) as reviews from reviews group by platform"`.

## Gotchas

- These are real reviews. Select counts and statuses, never `text` or `title`. `stop` deletes them with the home.
- Google Play's list shifts between calls, so a second run seconds later can insert a few different reviews. Seen 2026-11-24: 73, then 0, then 4, with no duplicates.
- The App Store feed can hold nothing for the last days. `inserted: 0` with status `ok` is a pass.
- `backfill` and `reconcile` fetch months of reviews. Run them only when the change concerns them.
