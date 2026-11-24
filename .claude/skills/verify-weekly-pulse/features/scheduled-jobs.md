# Run scheduled jobs

Plans which app gets which job, runs one job for one app, and prints a job's log only when it holds nothing private.

## Sub-features

- `jobs-plan` maps a cron or a dispatch to jobs.
- `jobs-refuse` rejects a backfill with no app and an unknown app.
- `jobs-pulse` publishes the latest complete week.
- `jobs-log` shows a clean log and withholds one with review text.

## How to get to it (user POV)

- The three schedules in `.github/workflows/pulse.yml`.
- A manual dispatch of that workflow with `mode` and `app_key`.
- Both run `python -m src.scheduler plan | run | show-log`, driven here.

## Driving it with verify.py

Preconditions:

- Baseline state.

- **Plan daily.** `python $V cli --run $RUN --name plan-daily --env GITHUB_EVENT_NAME=schedule --env "PULSE_SCHEDULE=30 20 * * *" -- src.scheduler plan`. Exit 0, one job `groww`/`daily`, and the same list in the evidence's `github_output`.
- **Plan weekly.** Same with `--name plan-weekly` and `PULSE_SCHEDULE=30 3 * * 1`. One job `groww`/`pulse`.
- **Plan monthly.** Same with `--name plan-monthly` and `PULSE_SCHEDULE=30 21 1 * *`. One job `groww`/`reconcile`.
- **Plan a dispatch.** `python $V cli --run $RUN --name plan-dispatch --env GITHUB_EVENT_NAME=workflow_dispatch --env PULSE_MODE=backfill --env PULSE_APP_KEY=groww -- src.scheduler plan`. One job `groww`/`backfill`.
- **Refuse a backfill with no app.** `python $V cli --run $RUN --name plan-backfill --env GITHUB_EVENT_NAME=workflow_dispatch --env PULSE_MODE=backfill -- src.scheduler plan`. Exit 2 with a message naming `app_key`.
- **Refuse an unknown app.** `python $V cli --run $RUN --name unknown -- src.scheduler run --app nope --mode pulse`. Exit 2.
- **Pulse job.** `python $V cli --run $RUN --name pulse -- src.scheduler run --app groww --mode pulse`. Exit 0, `status` is `published` or `low_volume`, and `week_start` is the Monday of the latest complete week (UTC). `python $V composio --run $RUN --name google` agrees: one unsent draft, or nothing for `low_volume`.
- **Clean log.** `python $V cli --run $RUN --name log-clean -- src.scheduler show-log --app groww --file .claude/skills/verify-weekly-pulse/runs/$RUN/evidence/001-seed.json`. Exit 0 and the file is printed.
- **Leaking log.** `python $V cli --run $RUN --name log-leak -- src.scheduler show-log --app groww --file .claude/skills/verify-weekly-pulse/runs/$RUN/home/data/raw/groww/play_reviews_2026-08-24_2026-11-15.csv`. Exit 3, `withheld`, and no review text in stdout or stderr.

## Gotchas

- The pulse job uses today's date. The baseline reviews end on 2026-11-09, so once fewer than 30 fall in the 12-week window the expected status is `low_volume`. Prove `published` through [Publish the weekly pulse](./publish-weekly-pulse.md) then.
- `show-log` compares against reviews in a similar moving window, so `log-leak` stops firing once the baseline leaves it.
- The matrix, secrets and concurrency of GitHub Actions are not exercised.
