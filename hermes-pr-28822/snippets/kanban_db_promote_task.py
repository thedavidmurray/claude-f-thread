"""
Paste the `promote_task` function into hermes_cli/kanban_db.py.

Insertion point: anywhere among the public task-state functions (block_task,
unblock_task, complete_task). Recommended: directly after `unblock_task`
(grouped with the other manual state-transition verbs).

This function follows the file's existing conventions:
  * write_txn() context manager for atomic transactions
  * _append_event() for audit trail (already defined in the file)
  * Returns (bool, error) tuple — same shape as block_task / unblock_task
  * No printing, no I/O — pure DB mutation; the CLI layer formats output

The 'promoted_manual' event kind is intentionally distinct from the
existing 'promoted' kind (which recompute_ready emits for automatic
todo->ready transitions) so audit consumers can filter manual from
automatic promotions.
"""

# === BEGIN PASTE ===

def promote_task(
    conn: sqlite3.Connection,
    task_id: str,
    *,
    actor: str,
    reason: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> tuple[bool, str | None]:
    """Manually promote a `todo` or `blocked` task to `ready`.

    Mirrors the automatic promotion done by ``recompute_ready`` but
    drives it from a deliberate operator action (CLI / dashboard /
    orchestrator) with an audit-trail entry.

    Refuses to promote if any parent dep is not in a terminal state
    (`done` / `archived`) unless ``force=True``. Does NOT change
    assignee or claim state — the dispatcher still picks the card up
    in the normal way.

    Returns ``(True, None)`` on success and ``(False, reason)`` if
    the promotion was refused. ``dry_run=True`` validates the
    promotion would succeed without mutating state.
    """
    row = conn.execute(
        "SELECT status FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    if row is None:
        return False, f"task {task_id} not found"

    cur_status = row["status"]
    if cur_status not in ("todo", "blocked"):
        return False, (
            f"task {task_id} is {cur_status!r}; promote only applies to "
            f"'todo' or 'blocked'"
        )

    if not force:
        parents = conn.execute(
            "SELECT t.id, t.status FROM tasks t "
            "JOIN task_links l ON l.parent_id = t.id "
            "WHERE l.child_id = ?",
            (task_id,),
        ).fetchall()
        unsatisfied = [
            p["id"] for p in parents
            if p["status"] not in ("done", "archived")
        ]
        if unsatisfied:
            return False, (
                f"unsatisfied parent dependencies: "
                f"{', '.join(unsatisfied)} (use --force to override)"
            )

    if dry_run:
        return True, None

    with write_txn(conn):
        upd = conn.execute(
            "UPDATE tasks SET status = 'ready' "
            "WHERE id = ? AND status IN ('todo', 'blocked')",
            (task_id,),
        )
        if upd.rowcount != 1:
            return False, f"task {task_id} status changed during promotion"
        _append_event(
            conn,
            task_id,
            "promoted_manual",
            {"actor": actor, "reason": reason, "forced": force},
        )

    return True, None

# === END PASTE ===
