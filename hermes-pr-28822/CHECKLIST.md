# Pre-submit checklist

## Before opening the PR

- [ ] On `feat/kanban-promote-cli` branch (NOT `claude/hermes-kanban-pr1-gS5hC`)
- [ ] `git fetch upstream && git rebase upstream/main` — this file got 10 commits in 1 day on May 19, 2026, re-verify against latest
- [ ] `scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -q` passes
- [ ] `scripts/run_tests.sh tests/hermes_cli/ -q` passes (no regressions in sibling tests)
- [ ] Manual smoke per `PR_BODY.md` "How to test" section, on at least one platform
- [ ] No `~/.hermes` hardcoded paths added (use `get_hermes_home()` if needed)
- [ ] Commit message uses Conventional Commits: `feat(cli): kanban promote verb for manual todo->ready recovery`
- [ ] PR is one logical change (just the promote verb — no drive-by cleanups)
- [ ] PR description includes "How to test", "Platforms tested", "Related issue: #28822"

## Exact insertion points

### `hermes_cli/kanban_db.py`

1. Paste the `promote_task` function from `snippets/kanban_db_promote_task.py`.
   - Location: grouped with `block_task` / `unblock_task` / `complete_task`. Best landing: directly after the function `unblock_task`.
   - Verify the `_append_event` call site matches the signature in your checkout:
     ```python
     def _append_event(conn, task_id, kind, payload=None, *, run_id=None)
     ```
     If upstream has changed this signature, update the call.

### `hermes_cli/kanban.py`

1. Paste PART 1 (subparser) inside `build_parser()` next to the existing `p_block` / `p_unblock` registrations.
2. Paste PART 2 (`_cmd_promote` handler) at module level near `_cmd_block` / `_cmd_unblock`.
3. If kanban.py uses a `COMMANDS` dispatch dict, add `"promote": _cmd_promote`. If it dispatches via `getattr(module, f"_cmd_{action}")`, no extra wiring needed.

### `tests/hermes_cli/test_kanban_promote.py`

1. Copy the file from `tests/test_kanban_promote.py` in this package.
2. Verify the autouse `_isolate_hermes_home` fixture in `tests/conftest.py` is in effect (it should be — per AGENTS.md).

## Known assumptions to verify in your checkout

These were inferred from public reads of `main` on 2026-05-20 and may have drifted:

| Assumption | Where to verify |
|---|---|
| `create_task` returns the task id as `str` (not an object with `.id`) and takes `initial_status="todo"` (not `status=`) | `def create_task(...) -> str:` in `kanban_db.py` |
| `block_task(conn, tid, *, reason=..., expected_run_id=None)` | `def block_task` in `kanban_db.py` |
| `_append_event(conn, task_id, kind, payload_dict, *, run_id=None)` — note positional args, dict (not pre-serialized) payload | `def _append_event` in `kanban_db.py` |
| `_profile_author()` helper exists in `kanban.py` and returns a string | grep `_profile_author` in `kanban.py` |
| `write_txn` is exported / accessible inside `promote_task` | `@contextlib.contextmanager def write_txn` in `kanban_db.py` |

If any has changed, adjust the snippet before pasting.

## After opening the PR

- [ ] Add a short comment on issue #28844 noting that commit `7c622b6` ("fix(kanban): migrate task session index after columns") appears to have already fixed it — request the issue be closed. This is a high-signal contribution gesture.
