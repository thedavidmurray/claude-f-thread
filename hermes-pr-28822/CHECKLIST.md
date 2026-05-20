# Pre-submit checklist

## Sandbox verification status (2026-05-20)

The entire package was applied to a fresh shallow clone of `main` and verified:

- ✅ **All 11 unit tests pass** under `scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -v` (4 xdist workers, hermetic env)
- ✅ **No regressions** in sibling kanban tests (368/370 pass; the 2 failures are pre-existing — missing optional `fastapi` for the dashboard plugin, unrelated to this PR)
- ✅ **CLI smoke** verified end-to-end: `hermes kanban promote` succeeds with parent done, refuses cleanly with parent not done, `--force` overrides, `--dry-run` reports without mutating, `--json` formats correctly, audit events written with `kind='promoted_manual'` and correct payload

## Before opening the PR

- [ ] On `feat/kanban-promote-cli` branch (NOT `claude/hermes-kanban-pr1-gS5hC` — that's the staging branch in the scratch repo)
- [ ] `git fetch upstream && git rebase upstream/main` — this file got 10 commits in 1 day on May 19, 2026, re-verify against latest
- [ ] `scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -q` passes
- [ ] `scripts/run_tests.sh tests/hermes_cli/ -q` passes (no regressions — expect 2 pre-existing `fastapi`-missing failures unrelated to this PR)
- [ ] Manual smoke per `PR_BODY.md` "How to test" section, on at least one platform
- [ ] Commit message uses Conventional Commits: `feat(cli): kanban promote verb for manual todo->ready recovery`
- [ ] PR is one logical change (just the promote verb — no drive-by cleanups)

## Verified insertion points (commit chain ending at 34120a0)

### `hermes_cli/kanban_db.py`

- Paste `promote_task` from `snippets/kanban_db_promote_task.py` **immediately before** `def unblock_task(...)` (line ~3033).
- Required imports already present at file head: `sqlite3`, `json`, `Optional`, `Iterable`.
- Uses `write_txn` (defined in same file) and `_append_event` (defined in same file).

### `hermes_cli/kanban.py`

- PART 1 (subparser): paste **immediately before** `p_archive = sub.add_parser("archive", ...)` (line ~553).
- PART 2 (`_cmd_promote` handler): paste **immediately before** `def _cmd_archive(args: argparse.Namespace) -> int:` (line ~1961).
- PART 3 (dispatch): inside the `handlers = { ... }` dict (line ~899), add `"promote":  _cmd_promote,` **immediately after** `"unblock":  _cmd_unblock,`.

### `tests/hermes_cli/test_kanban_promote.py`

- Drop the file from `tests/test_kanban_promote.py` in this package directly into `tests/hermes_cli/`.
- The file defines its own `kanban_home` fixture matching the per-file pattern used by `test_kanban_db.py` — does NOT rely on a global autouse fixture.

## Verified signatures (do NOT need to re-verify unless main has churned)

| Symbol | Signature |
|---|---|
| `kb.create_task` | `(conn, *, title, body=None, assignee=None, ..., initial_status='running', parents=(), ...) -> str` — returns task id |
| `kb.block_task` | `(conn, task_id, *, reason=None, expected_run_id=None) -> bool` |
| `kb.get_task` | `(conn, task_id) -> Task` (dataclass with `.id`, `.status`, `.assignee`, ...) |
| `kb._append_event` | `(conn, task_id, kind, payload=None, *, run_id=None) -> None` — payload is a dict, not pre-serialized |
| `kb.write_txn` | `@contextlib.contextmanager` doing `BEGIN IMMEDIATE` |
| `kb._INITIALIZED_PATHS` | module-level set; tests `.discard(str(path.resolve()))` to force re-init |
| `_profile_author()` | helper in `kanban.py`; returns `HERMES_PROFILE_NAME` env or `'user'` |

## Semantics gotchas that bit my first draft

- `create_task` rejects `initial_status='todo'` — only `{'blocked', 'running'}` are valid. **`todo` is set automatically** when the task has not-yet-done parents.
- To construct a "stuck todo" task in tests, create parents, create child with `parents=[...]`, then direct-`UPDATE` the parent status to `done`. This simulates the #28822 race deterministically.
- A non-parent task auto-promotes to `ready` immediately; `promote` correctly refuses it with "promote only applies to 'todo' or 'blocked'".

## After opening the PR

- [ ] Comment on issue #28844 noting commit `7c622b6` ("fix(kanban): migrate task session index after columns") already addressed the bug — request the issue be closed. Adjacent goodwill gesture.
