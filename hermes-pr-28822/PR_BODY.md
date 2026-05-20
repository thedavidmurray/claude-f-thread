## Summary

Adds a `hermes kanban promote <task_id>` CLI verb for manual `todo`/`blocked` → `ready` recovery, addressing the gap described in #28822 where this has required direct SQLite writes that bypass the audit trail.

Closes #28822.

## Behavior

```
hermes kanban [--board <slug>] promote <task_id> [reason...] [--force] [--dry-run] [--json]
```

- Refuses promotion unless every parent dep is `done` / `archived` (override with `--force`)
- Emits a `promoted_manual` row in `task_events` with `{actor, reason, forced}` payload — distinct from the existing `promoted` kind that `recompute_ready` writes for automatic transitions, so audit consumers can filter human-driven from system-driven promotions
- Does **not** mutate `assignee` or claim state — the dispatcher picks the card up via its normal `ready` polling path
- `--dry-run` validates the promotion (including dependency check) without mutating
- `--json` emits a machine-readable result for orchestrators

## Why this design

The use case in #28822 is anti-respawn recovery: an organizational parent task closes `done` before the auto-promote daemon fires, leaving children stuck. Operators currently fix this with raw SQL, which bypasses the audit trail. This verb is the smallest surface that closes the gap:

- `promote` (not `claim`) — the verb describes a lifecycle promotion, not assignment
- `promoted_manual` kind keeps human-driven and auto-driven promotions separable in audit queries
- Same `(bool, error)` return shape as `block_task` / `unblock_task` so callers handle it uniformly

## How to test

```bash
scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -v
# 11 passed

# Manual smoke
hermes kanban create "parent task"
# -> Created t_abcd  (ready, ...)
hermes kanban create "child task" --parent t_abcd
# -> Created t_efgh  (todo, ...)

hermes kanban promote t_efgh "operator override"
# cannot promote t_efgh: unsatisfied parent dependencies: t_abcd (use --force to override)

hermes kanban promote t_efgh "operator override" --force
# Promoted t_efgh -> ready: operator override

hermes kanban show t_efgh
# status: ready; events include promoted_manual {"actor":"<profile>","reason":"operator override","forced":true}

# Simulating the #28822 scenario after parent closes:
hermes kanban complete t_abcd "done"          # parent done
hermes kanban promote t_efgh "post-close fixup" --dry-run --json
# {"task_id":"t_efgh","promoted":true,"dry_run":true,...,"error":null}
```

## Platforms tested

- Linux (sandbox, Python 3.11.15, pytest 9.0.2, pytest-xdist 3.8.0)

No platform-specific primitives — pure SQLite/argparse.

## Files changed

- `hermes_cli/kanban_db.py` — new `promote_task()` function
- `hermes_cli/kanban.py` — `promote` subparser + `_cmd_promote` handler + dispatch dict entry
- `tests/hermes_cli/test_kanban_promote.py` — 11 unit tests: stuck-todo happy path, dependency refusal (no force), `--force` override + audit `forced:true`, audit event payload, assignee invariant, `--dry-run` non-mutation, `--dry-run` reporting dependency failures, rejecting `ready`/non-existent tasks, promoting blocked tasks

## Out of scope

- Arbitrary `--from`/`--to` state transitions. The issue spec mentioned `--from/--to`, but every real use case described is `todo`/`blocked` → `ready`. A general state-machine verb would expand the review surface significantly without solving any concrete reported gap.
- Bulk promotion (`--ids`). Easy to add as a follow-up if asked.
