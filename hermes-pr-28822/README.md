# PR package: `feat(cli): kanban promote verb for manual todo→ready recovery`

Target repo: `NousResearch/hermes-agent`
Target issue: [#28822](https://github.com/NousResearch/hermes-agent/issues/28822)
Branch name (per CONTRIBUTING.md): `feat/kanban-promote-cli`

## Why this PR over the original 5-PR plan

The original plan was QC'd against the live repo and the proposed PRs were either already shipped or based on misreadings:

| Original PR | Status |
|---|---|
| #1 sequential identifiers | Already shipped — tasks have `t_<4-hex>` IDs via `_new_task_id()` |
| #2 labels | Possibly viable but crowded with `skills`/`tenant`/`session_id` already |
| #3 board metadata | Already shipped — `board.json` per board |
| #4 auto-recovery | Already shipped AND opposite of what maintainers want (see open bugs #29014, #28944, #28903 — auto-recovery is currently *too* aggressive) |
| #5 Paperclip bridge | Misread — Paperclip is a competitor in a comparative analysis, not an integration target |

Also flagged: issue **#28844** (schema index ordering) is already fixed in main by commit `7c622b6` ("fix(kanban): migrate task session index after columns") but never closed. Worth a "appears fixed by 7c622b6 — please close" comment.

## What this PR delivers

A new `hermes kanban promote <task_id>` CLI verb that manually moves a task from `todo`/`blocked` to `ready`, with audit-trail events and the safety rails the issue asks for. Spec from #28822 implemented:

- `--reason "..."` recorded in the `task_events` audit trail
- `--force` to bypass parent-dependency checks
- `--dry-run` to preview without mutation
- `--json` for machine-readable output
- Refuses promotion unless all parents are `done`/`archived` (unless `--force`)
- Emits `task_events` with `kind='promoted_manual'` and actor/reason payload
- Does NOT implicitly assign the card (per issue)

## Files in this package

- `snippets/kanban_db_promote_task.py` — paste into `hermes_cli/kanban_db.py` after `block_task`
- `snippets/kanban_cli_promote_verb.py` — paste the subparser block + handler into `hermes_cli/kanban.py`
- `tests/test_kanban_promote.py` — drop into `tests/hermes_cli/test_kanban_promote.py`
- `PR_BODY.md` — paste into the PR description
- `CHECKLIST.md` — final verification before submitting

## Transfer instructions (from desktop)

```bash
# 1. Fork NousResearch/hermes-agent on GitHub, then:
git clone git@github.com:<you>/hermes-agent.git
cd hermes-agent
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git fetch upstream
git checkout -b feat/kanban-promote-cli upstream/main

# 2. Set up the venv per CONTRIBUTING.md (prefer .venv over venv)
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 3. Apply snippets to source files (see CHECKLIST.md for exact insertion points).

# 4. Drop the test file in:
cp /path/to/this/package/tests/test_kanban_promote.py tests/hermes_cli/

# 5. Run the hermetic test wrapper (NOT raw pytest)
scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -q

# 6. Manually test per the verification steps in CHECKLIST.md.

# 7. Commit with Conventional Commits format
git add -A
git commit -m "feat(cli): kanban promote verb for manual todo->ready recovery"
git push -u origin feat/kanban-promote-cli

# 8. Open the PR with body from PR_BODY.md. Link issue #28822.
```

## ⚠️ Re-verify before pushing

This file got 10 commits in 1 day on May 19, 2026. The codebase moves fast. Before pushing, fetch latest `upstream/main` and re-run `scripts/run_tests.sh` against your branch.
