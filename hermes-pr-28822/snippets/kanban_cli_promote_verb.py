"""
Paste these THREE blocks into hermes_cli/kanban.py.

Verified against main on 2026-05-20 (commit chain ending at 34120a0).
Tested end-to-end in a sandbox with `scripts/run_tests.sh` — 11/11 tests
pass, manual CLI smoke succeeds for --json / --force / --dry-run / refusal.

PART 1 — subparser registration. Insertion point: inside `build_parser()`,
directly before `p_archive = sub.add_parser("archive", ...)`.

PART 2 — handler function. Insertion point: directly before
`def _cmd_archive(args: argparse.Namespace) -> int:`.

PART 3 — dispatch wiring. There's an explicit handler dict around line
~899 (`handlers = { "block": _cmd_block, ... }`). Add the promote entry
directly after `"unblock":  _cmd_unblock,`.
"""

# ============================================================
# PART 1 — subparser registration (paste inside build_parser)
# ============================================================

# === BEGIN PASTE 1 ===

p_promote = sub.add_parser(
    "promote",
    help="Manually move a todo/blocked task to ready (recovery path)",
)
p_promote.add_argument("task_id")
p_promote.add_argument(
    "reason",
    nargs="*",
    help="Audit-trail reason (recorded on the task_events row)",
)
p_promote.add_argument(
    "--force",
    action="store_true",
    help="Promote even if parent dependencies are not yet done/archived",
)
p_promote.add_argument(
    "--dry-run",
    action="store_true",
    help="Validate the promotion without mutating state",
)
p_promote.add_argument(
    "--json",
    dest="json",
    action="store_true",
    help="Emit machine-readable JSON result",
)

# === END PASTE 1 ===


# ============================================================
# PART 2 — handler function
# ============================================================

# === BEGIN PASTE 2 ===

def _cmd_promote(args: argparse.Namespace) -> int:
    reason = " ".join(args.reason).strip() if args.reason else None
    author = _profile_author()
    as_json = getattr(args, "json", False)
    with kb.connect() as conn:
        ok, err = kb.promote_task(
            conn,
            args.task_id,
            actor=author,
            reason=reason,
            force=bool(args.force),
            dry_run=bool(args.dry_run),
        )
    if as_json:
        print(json.dumps(
            {
                "task_id": args.task_id,
                "promoted": ok,
                "dry_run": bool(args.dry_run),
                "forced": bool(args.force),
                "reason": reason,
                "error": err,
            },
            indent=2,
            ensure_ascii=False,
        ))
        return 0 if ok else 1
    if not ok:
        print(f"cannot promote {args.task_id}: {err}", file=sys.stderr)
        return 1
    tag = " (dry)" if args.dry_run else ""
    label = "Would promote" if args.dry_run else "Promoted"
    print(f"{label} {args.task_id} -> ready{tag}"
          + (f": {reason}" if reason else ""))
    return 0

# === END PASTE 2 ===


# ============================================================
# PART 3 — dispatch wiring (one line, in the existing handlers dict)
# ============================================================

# === BEGIN PASTE 3 ===

        "promote":  _cmd_promote,

# === END PASTE 3 ===
