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

The fastest path uses the pre-generated patch (`hermes-kanban-promote.patch`). It applies cleanly against `main` of `NousResearch/hermes-agent` as of 2026-05-20.

```bash
# 1. Fork NousResearch/hermes-agent on GitHub via the web UI, then:
git clone git@github.com:<your-gh-username>/hermes-agent.git
cd hermes-agent
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git fetch upstream
git checkout -b feat/kanban-promote-cli upstream/main

# 2. Download the patch from the scratch repo (one of):
#    a) Browse to the scratch PR, copy hermes-kanban-promote.patch
#    b) Or curl it from the raw URL once you've located the file in PR #1
curl -fsSLO https://raw.githubusercontent.com/thedavidmurray/claude-f-thread/claude/hermes-kanban-pr1-gS5hC/hermes-pr-28822/hermes-kanban-promote.patch

# 3. Apply it
git apply hermes-kanban-promote.patch
# (dry-run first with --check if you want)

# 4. Set up venv per CONTRIBUTING.md
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 5. Run the test the way CI will run it (verified passing in sandbox)
scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -v
# expect: 11 passed

# 6. Commit (Conventional Commits format)
git add hermes_cli/kanban.py hermes_cli/kanban_db.py tests/hermes_cli/test_kanban_promote.py
git commit -m "feat(cli): kanban promote verb for manual todo->ready recovery"
git push -u origin feat/kanban-promote-cli

# 7. Open the PR via web UI:
#    Base: NousResearch/hermes-agent main
#    Head: <your-gh-username>/hermes-agent feat/kanban-promote-cli
#    Body: paste from PR_BODY.md
#    Link issue #28822 in the body
```

If the patch fails to apply because upstream has churned, the snippets in `snippets/` and the verified insertion points in `CHECKLIST.md` are the fallback — they're more robust to file shifts than the patch.

## Fallback (if patch doesn't apply)

## ✅ Sandbox-verified (2026-05-20)

Applied the entire package to a fresh shallow clone of `main`, installed with `pip install -e ".[dev]"`, and ran:

- `scripts/run_tests.sh tests/hermes_cli/test_kanban_promote.py -v` → **11/11 pass**
- `scripts/run_tests.sh tests/hermes_cli/{test_kanban_db,test_kanban_db_init,test_kanban_core_functionality,test_kanban_cli}.py -q` → 368/370 pass (the 2 failures are pre-existing — missing optional `fastapi` for the dashboard plugin, unrelated to this PR)
- Manual CLI smoke: `hermes kanban promote` works end-to-end for refuse/--force/--dry-run/--json/audit-event

See `CHECKLIST.md` for verified insertion points and signature reference.

## ⚠️ Re-verify before pushing

This file got 10 commits in 1 day on May 19, 2026. The codebase moves fast. Before pushing, fetch latest `upstream/main` and re-run `scripts/run_tests.sh` against your branch.
