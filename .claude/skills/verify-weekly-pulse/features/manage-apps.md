# Manage apps

Lets an operator search both stores, register up to five live apps, rename one, replace one and archive one. Anyone may read the list, and only an operator may change it over HTTP.

## Sub-features

- `apps-list` shows live apps and used slots, and archived apps on request.
- `apps-search` returns up to three matches per store.
- `apps-register` verifies the listings and queues a backfill.
- `apps-reject` refuses a missing listing and a listing already in use.
- `apps-rename` changes the display name and nothing else.
- `apps-replace` archives one app and registers another in its slot.
- `apps-archive` frees the slot and keeps the record.
- `apps-auth` refuses anonymous callers and non-operators.
- `apps-dashboard` does all of it on the `/manage` page after an operator signs in by email link.

## How to get to it (user POV)

- CLI: `python -m src.registry list | search | add | rename | archive`.
- HTTP: `GET /apps`, `POST /search`, `POST /apps`, `PATCH /apps/{key}`, `POST /apps/{key}/replace`, `DELETE /apps/{key}`.
- Dashboard: side menu > Manage Apps, or app picker > Manage apps.

## Driving it with verify.py

Preconditions:

- Baseline state.
- Internet for search, register and replace.

- **List.** `python $V cli --run $RUN --name list -- src.registry list` and `python $V http --run $RUN --name apps GET /apps`. Both show only `groww` and one used slot.
- **Refuse strangers.** `python $V http --run $RUN --name rename-anon --body '{"display_name":"X"}' PATCH /apps/groww` gives 401. The same with `--name rename-outsider --as outsider` gives 403. `GET /apps` still shows `Groww`.
- **Rename over HTTP.** `python $V http --run $RUN --name rename --as operator --body '{"display_name":"Groww App"}' PATCH /apps/groww` gives 200 and only `display_name` differs.
- **Rename from the CLI.** `python $V cli --run $RUN --name rename-back -- src.registry rename --app groww --name Groww`. Exit 0, and `GET /apps` shows `Groww`.
- **Reject no listing.** `python $V http --run $RUN --name no-listing --as operator --body '{"display_name":"Nothing"}' POST /apps` gives 422.
- **Reject a taken listing.** `python $V http --run $RUN --name taken --as operator --body '{"display_name":"Groww Two","play_package_id":"com.nextbillion.groww"}' POST /apps` gives 409 and names the owner.
- **Search from the CLI, live.** `python $V cli --run $RUN --name search -- src.registry search --name "Zerodha Coin"`. Exit 0, `no_matches` false, both stores listed.
- **Search over HTTP, live.** `python $V http --run $RUN --name search-http --as operator --body '{"name":"Zerodha Coin"}' POST /search` gives 200.
- **Register from the CLI, live.** `python $V cli --run $RUN --name add -- src.registry add --name "Zerodha Coin" --play com.zerodha.coin`. Exit 0, status `pending_backfill`, `slots_used` 2, and the backfill message says it is queued for the next daily run.
- **Replace over HTTP, live.** `python $V http --run $RUN --name replace --as operator --body '{"display_name":"Zerodha Kite","play_package_id":"com.zerodha.kite3"}' POST /apps/zerodha-coin/replace` gives 201, and `slots_used` stays 2.
- **Archive over HTTP.** `python $V http --run $RUN --name archive-http --as operator DELETE /apps/zerodha-kite` gives 200 and status `archived`.
- **Register over HTTP, live.** `python $V http --run $RUN --name register-http --as operator --body '{"display_name":"Zerodha Kite","play_package_id":"com.zerodha.kite3"}' POST /apps` gives 201 with `app_key` `zerodha-kite-2`, because archived keys are never reused.
- **Archive from the CLI.** `python $V cli --run $RUN --name archive -- src.registry archive --app zerodha-kite-2`. Exit 0 and status `archived`. `python $V cli --run $RUN --name list-archived -- src.registry list --include-archived` shows the archived apps and one used slot.
- **Proof.** `python $V db --run $RUN --name rows "select app_key, display_name, status from apps"` matches the last list.
- **Dashboard, signed out.** Start the API and the dashboard as README step 4 says and open `/manage`. The live and archived apps and the slot counter show, with a sign-in form and no Add, Rename, Replace or Archive button.
- **Dashboard, signed in.** Sign in with an operator's email link. Add an app: search, choose one listing per store, press Review, and check with `GET /apps` that nothing is registered yet. Press Add app, and the slot counter rises by one. Rename, replace and archive it. Keep a screenshot of the review step and of the archive confirmation.

## Gotchas

- Review must not register anything. Check it in a real browser: jsdom does not reproduce the fault it guards against.
- The CLI has no sign-in. Auth is proven only over HTTP.
- Backfill dispatch is `not_configured` in a run, so no GitHub workflow can start.
- The store chooses search results, so assert the shape, not the ranking.
- The five-app cap needs four more live registrations. `tests/test_phase7_store.py` proves it without the network.
