"""
Paste these two blocks into hermes_cli/kanban.py.

PART 1 — subparser registration. Insertion point: inside `build_parser()`,
grouped with the other state-transition verbs. Recommended: directly after
the `unblock` subparser registration.

PART 2 — handler function. Insertion point: anywhere among the existing
`_cmd_*` functions. Recommended: directly after `_cmd_unblock`.

PART 3 — dispatch wiring. If kanban.py has an explicit handler map
(`COMMANDS = {"block": _cmd_block, ...}`), add `"promote": _cmd_promote`
there. If it uses `args.kanban_action` lookup via `globals()` or
`getattr`, no additional wiring is needed.
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
# PART 2 — handler function (paste at module level near other _cmd_*)
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
