"""Tests for the kanban `promote` verb (issue #28822).

Conventions followed (from AGENTS.md / CONTRIBUTING.md):
  * stdlib + pytest + unittest.mock only — no live network
  * relies on the autouse `_isolate_hermes_home` fixture in tests/conftest.py
    to redirect HERMES_HOME to a temp dir
  * no hardcoded ~/.hermes paths — uses kb.connect() default, which routes
    through the isolated home
"""

from __future__ import annotations

import json

import pytest

from hermes_cli import kanban_db as kb


@pytest.fixture()
def conn():
    """Open a fresh kanban DB rooted at the isolated HERMES_HOME."""
    with kb.connect() as c:
        yield c


def _mk(conn, **overrides):
    """Create a task with sane defaults; returns the task id."""
    defaults = dict(
        title="t",
        body="",
        assignee=None,
        initial_status="todo",
        priority=0,
        created_by="tester",
        tenant=None,
        parents=(),
        skills=None,
    )
    defaults.update(overrides)
    return kb.create_task(conn, **defaults)


def test_promote_todo_without_parents_succeeds(conn):
    tid = _mk(conn)
    ok, err = kb.promote_task(conn, tid, actor="tester")
    assert ok and err is None
    row = conn.execute(
        "SELECT status FROM tasks WHERE id = ?", (tid,)
    ).fetchone()
    assert row["status"] == "ready"


def test_promote_refuses_when_parent_not_done(conn):
    parent = _mk(conn, title="parent")
    child = _mk(conn, title="child", parents=(parent,))
    ok, err = kb.promote_task(conn, child, actor="tester")
    assert ok is False
    assert err is not None
    assert "unsatisfied parent dependencies" in err
    assert parent in err
    row = conn.execute(
        "SELECT status FROM tasks WHERE id = ?", (child,)
    ).fetchone()
    assert row["status"] == "todo"


def test_promote_with_force_bypasses_dependency_check(conn):
    parent = _mk(conn, title="parent")
    child = _mk(conn, title="child", parents=(parent,))
    ok, err = kb.promote_task(
        conn, child, actor="tester", reason="recovery", force=True
    )
    assert ok and err is None
    row = conn.execute(
        "SELECT status FROM tasks WHERE id = ?", (child,)
    ).fetchone()
    assert row["status"] == "ready"


def test_promote_emits_audit_event(conn):
    tid = _mk(conn)
    kb.promote_task(conn, tid, actor="tester", reason="manual recovery")
    ev = conn.execute(
        "SELECT kind, payload FROM task_events "
        "WHERE task_id = ? AND kind = 'promoted_manual'",
        (tid,),
    ).fetchone()
    assert ev is not None
    payload = json.loads(ev["payload"])
    assert payload["actor"] == "tester"
    assert payload["reason"] == "manual recovery"
    assert payload["forced"] is False


def test_promote_does_not_change_assignee(conn):
    tid = _mk(conn, assignee=None)
    kb.promote_task(conn, tid, actor="tester")
    row = conn.execute(
        "SELECT assignee FROM tasks WHERE id = ?", (tid,)
    ).fetchone()
    assert row["assignee"] is None


def test_promote_dry_run_validates_without_mutation(conn):
    tid = _mk(conn)
    ok, err = kb.promote_task(conn, tid, actor="tester", dry_run=True)
    assert ok and err is None
    row = conn.execute(
        "SELECT status FROM tasks WHERE id = ?", (tid,)
    ).fetchone()
    assert row["status"] == "todo"
    ev = conn.execute(
        "SELECT COUNT(*) AS n FROM task_events "
        "WHERE task_id = ? AND kind = 'promoted_manual'",
        (tid,),
    ).fetchone()
    assert ev["n"] == 0


def test_promote_dry_run_reports_dependency_failure(conn):
    parent = _mk(conn, title="parent")
    child = _mk(conn, title="child", parents=(parent,))
    ok, err = kb.promote_task(conn, child, actor="tester", dry_run=True)
    assert ok is False
    assert err is not None
    assert "unsatisfied" in err


def test_promote_rejects_non_todo_status(conn):
    tid = _mk(conn)
    kb.promote_task(conn, tid, actor="tester")
    ok, err = kb.promote_task(conn, tid, actor="tester")
    assert ok is False
    assert "'ready'" in err and "promote only applies" in err


def test_promote_rejects_unknown_task(conn):
    ok, err = kb.promote_task(conn, "t_doesnotexist", actor="tester")
    assert ok is False
    assert "not found" in err


def test_promote_blocked_task_works(conn):
    tid = _mk(conn)
    # block_task signature: (conn, task_id, *, reason, expected_run_id=None)
    kb.block_task(conn, tid, reason="manual", expected_run_id=None)
    ok, err = kb.promote_task(conn, tid, actor="tester", reason="ready now")
    assert ok and err is None
    row = conn.execute(
        "SELECT status FROM tasks WHERE id = ?", (tid,)
    ).fetchone()
    assert row["status"] == "ready"
