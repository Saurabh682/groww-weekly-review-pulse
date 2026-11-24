# Weekly Review Pulse verification map

The maintained source for verifying user-facing behavior. Read this index, then use the matching feature file as the recipe.

## Baseline preconditions

- `python $V launch --run $RUN` exited 0 and `python $V doctor --run $RUN` is healthy.
- Groww is the only app, status `active`, with the baseline reviews for week `2026-11-09`.
- Nothing is published yet.
- Features marked **live** need internet and the stores to answer.

## Driving conventions

- Start each recipe from a freshly launched run unless it says otherwise.
- `$V` and `$RUN` are set as in `SKILL.md`. Commands are literal.
- Each step needs its own `--name`. Evidence is numbered in order.

## Proof and skip reporting

- CLI proof: command, stdout, stderr and exit code. HTTP proof: request, caller, status and body. Both are saved for you.
- Mutation proof adds a second view: `composio`, `db`, or a later read through the other surface.
- Name the feature id and entry point when reporting.
- Report an unreachable path with the attempted command and the unmet precondition. A skipped entry point is not verified by a different one.

## Feature entry contract

Each file has an H1, one paragraph, then exactly these H2s in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with verify.py`, `Gotchas`.

## Features

- [Publish the weekly pulse](./publish-weekly-pulse.md): dry run, first publish, unchanged rerun, changed rerun.
- [Manage apps](./manage-apps.md): list, search, register, rename, archive, and who may do it. Live in part.
- [Read pulses](./read-pulses.md): apps, pulse history, one pulse, collection health.
- [Run scheduled jobs](./scheduled-jobs.md): planning, pulse job, log scan.
- [Collect reviews](./collect-reviews.md): daily collection from both stores. Live.
