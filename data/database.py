"""SQLite database layer — WAL mode, typed helpers."""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from data.schema import ALL_TABLES
from data.seed_data import SEED_FAILURE_EVENTS

DB_PATH = Path(__file__).resolve().parent.parent / "recovery.db"

# ── connection helper ─────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    """Return a WAL-mode connection with row-factory."""
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    return con


# ── bootstrap ─────────────────────────────────────────────────────────

def init_db(force_reseed: bool = False) -> None:
    """Create tables and optionally reseed."""
    con = _conn()
    for ddl in ALL_TABLES:
        con.execute(ddl)
    con.commit()
    if force_reseed:
        con.execute("DELETE FROM failure_events")
        con.execute("DELETE FROM hawkes_metrics")
        con.execute("DELETE FROM p2p_contracts")
        con.execute("DELETE FROM audit_log")
        con.commit()
    # seed only when table is empty
    row = con.execute("SELECT COUNT(*) FROM failure_events").fetchone()
    if row[0] == 0:
        for evt in SEED_FAILURE_EVENTS:
            insert_failure_event(evt, con=con)
    con.commit()
    con.close()


# ── failure_events CRUD ──────────────────────────────────────────────

def insert_failure_event(evt: dict, con: Optional[sqlite3.Connection] = None) -> None:
    """Insert one failure event row."""
    close = con is None
    if close:
        con = _conn()
    con.execute(
        """INSERT OR REPLACE INTO failure_events
           (event_id, customer_name, amount, bank, instrument_type,
            error_code, category, failed_at, status, resolved_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            evt["event_id"], evt["customer_name"], evt["amount"],
            evt["bank"], evt["instrument_type"], evt["error_code"],
            evt["category"], evt["failed_at"], evt["status"],
            evt.get("resolved_at"),
        ),
    )
    if close:
        con.commit()
        con.close()


def get_all_events() -> list[dict]:
    """Return all failure_events as dicts."""
    con = _conn()
    rows = con.execute("SELECT * FROM failure_events ORDER BY failed_at").fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_event(event_id: str) -> Optional[dict]:
    """Return a single event or None."""
    con = _conn()
    row = con.execute("SELECT * FROM failure_events WHERE event_id=?", (event_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def update_event_status(event_id: str, status: str, resolved_at: Optional[str] = None) -> None:
    """Update event status and optional resolved_at."""
    con = _conn()
    con.execute(
        "UPDATE failure_events SET status=?, resolved_at=? WHERE event_id=?",
        (status, resolved_at, event_id),
    )
    con.commit()
    con.close()


# ── hawkes_metrics ───────────────────────────────────────────────────

def insert_hawkes_metric(metric: dict) -> None:
    """Insert a computed Hawkes metric row."""
    con = _conn()
    con.execute(
        """INSERT INTO hawkes_metrics (event_id, computed_at, hazard_rate, next_retry_at, payroll_score)
           VALUES (?,?,?,?,?)""",
        (metric["event_id"], metric["computed_at"], metric["hazard_rate"],
         metric["next_retry_at"], metric["payroll_score"]),
    )
    con.commit()
    con.close()


def get_hawkes_metrics() -> list[dict]:
    """Return all hawkes_metrics rows."""
    con = _conn()
    rows = con.execute("SELECT * FROM hawkes_metrics ORDER BY computed_at").fetchall()
    con.close()
    return [dict(r) for r in rows]


# ── recovery stats ───────────────────────────────────────────────────

def get_recovery_stats() -> dict:
    """Aggregate stats for KPI cards."""
    con = _conn()
    total_at_risk = con.execute("SELECT COALESCE(SUM(amount),0) FROM failure_events").fetchone()[0]
    total_recovered = con.execute(
        "SELECT COALESCE(SUM(amount),0) FROM failure_events WHERE status='RECOVERED'"
    ).fetchone()[0]
    total_count = con.execute("SELECT COUNT(*) FROM failure_events").fetchone()[0]
    recovered_count = con.execute(
        "SELECT COUNT(*) FROM failure_events WHERE status='RECOVERED'"
    ).fetchone()[0]
    guardrail_count = con.execute(
        "SELECT COUNT(*) FROM audit_log WHERE guardrail_triggered IS NOT NULL"
    ).fetchone()[0]
    con.close()
    rate = (recovered_count / total_count * 100) if total_count else 0.0
    return {
        "total_at_risk": total_at_risk,
        "total_recovered": total_recovered,
        "recovery_rate": round(rate, 1),
        "guardrail_interventions": guardrail_count,
    }


# ── audit_log ────────────────────────────────────────────────────────

def log_audit_entry(
    event_id: str,
    action: str,
    reason: str,
    guardrail_triggered: Optional[str] = None,
    payload: Optional[dict] = None,
) -> None:
    """Append one immutable audit row."""
    con = _conn()
    con.execute(
        """INSERT INTO audit_log (log_id, event_id, timestamp, action, reason,
           guardrail_triggered, payload_json)
           VALUES (?,?,?,?,?,?,?)""",
        (
            f"LOG-{uuid.uuid4().hex[:12].upper()}",
            event_id,
            datetime.utcnow().isoformat(),
            action,
            reason,
            guardrail_triggered,
            json.dumps(payload) if payload else None,
        ),
    )
    con.commit()
    con.close()


def get_audit_log(event_id: Optional[str] = None, guardrail_only: bool = False) -> list[dict]:
    """Fetch audit rows with optional filters."""
    con = _conn()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params: list = []
    if event_id:
        query += " AND event_id=?"
        params.append(event_id)
    if guardrail_only:
        query += " AND guardrail_triggered IS NOT NULL"
    query += " ORDER BY timestamp DESC"
    rows = con.execute(query, params).fetchall()
    con.close()
    return [dict(r) for r in rows]


# ── p2p_contracts ────────────────────────────────────────────────────

def create_p2p_contract(contract: dict) -> None:
    """Insert a promise-to-pay contract."""
    con = _conn()
    con.execute(
        """INSERT OR REPLACE INTO p2p_contracts
           (contract_id, event_id, promised_date, raw_customer_text, confidence, status)
           VALUES (?,?,?,?,?,?)""",
        (
            contract["contract_id"], contract["event_id"],
            contract["promised_date"], contract["raw_customer_text"],
            contract["confidence"], contract["status"],
        ),
    )
    con.commit()
    con.close()


def get_p2p_contracts() -> list[dict]:
    """Return all P2P contracts."""
    con = _conn()
    rows = con.execute("SELECT * FROM p2p_contracts ORDER BY promised_date").fetchall()
    con.close()
    return [dict(r) for r in rows]
