## Summary

Adds a `hermes kanban promote <task_id>` CLI verb that manually moves a `todo` or `blocked` task to `ready`, addressing the gap described in #28822 where routine recovery has required direct SQLite writes.

Closes #28822.

## Behavior

```
hermes kanban [--board <slug>] promote <task_id> [reason...] [--force] [--dry-run] [--json]
```

- Refuses promotion unless every parent dep is `done` / `archived` (override with `--force`)
- Emits a `promoted_manual` row in `task_events` with `{actor, reason, forced}` payload — distinct from the existing `promoted` kind that `recompute_ready` writes for automatic transitions
- Does **not** mutate `assignee` or claim state — the dispatcher picks the card up via its normal `ready` polling path
- `--dry-run` validates the promotion would succeed (including the dependency check) without mutating
- `--json` emits a machine-readable result for orchestrators

## Why this design

Per the issue, the use case is anti-respawn recovery: an organizational parent closes `done` before the auto-promote logic fires, leaving children stuck. Operators currently fix this with raw SQL, which bypasses the audit trail. This verb is the smallest surface that closes the gap:

- `promote` (not `claim`) — the verb describes a lifecycle promotion, not assignment
- Manual `promoted_manual` kind keeps automated and human promotions separable in audit queries
- Same `(bool, error)` return shape as `block_task` / `unblock_task` so callers handle it uniformly

## How to test

```bash
scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -q

# Manual smoke
hermes kanban create "parent task"
# -> t_abcd
hermes kanban create "child task" --parent t_abcd
# -> t_efgh
hermes kanban promote t_efgh "operator override" --dry-run
# refuses with "unsatisfied parent dependencies: t_abcd"
hermes kanban promote t_efgh "operator override" --force
# Promoted t_efgh -> ready: operator override
hermes kanban show t_efgh
# status: ready; events show promoted_manual {actor, reason, forced:true}
```

## Platforms tested

- Linux (Ubuntu 24.04)
- macOS (Apple Silicon)

No platform-specific primitives — pure SQLite/argparse.

## Files changed

- `hermes_cli/kanban_db.py` — new `promote_task()` function
- `hermes_cli/kanban.py` — `promote` subparser + `_cmd_promote` handler
- `tests/hermes_cli/test_kanban_promote.py` — 10 unit tests covering happy path, dependency refusal, `--force`, `--dry-run`, audit-event payload, assignee invariant, error cases, and blocked-task promotion

## Out of scope

- Arbitrary `--from`/`--to` state transitions (e.g., `done` → `ready`). The issue spec mentioned `--from/--to`, but every real use case described is `todo`/`blocked` → `ready`. A general state-machine verb would expand the review surface significantly without solving any concrete reported gap.
- Bulk promotion (`--ids`). Easy to add as a follow-up if asked.
