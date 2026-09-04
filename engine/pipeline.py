"""Recovery pipeline — orchestrates Hawkes, Prospect, guardrails, and mocks."""

from datetime import datetime
from typing import Optional

from data import database as db
from engine.hawkes import HawkesScheduler
from engine.prospect import ProspectFramer
from engine.guardrails import GuardrailEngine, DEAD_ERROR_CODES
from services.razorpay_mock import create_payment_link, create_affordability_link
from services.rail_swap import generate_rail_swap_link
from utils import audit

_hawkes = HawkesScheduler()
_framer = ProspectFramer()
_guard = GuardrailEngine()


def run_recovery_pipeline(event_id: str) -> dict:
    """Execute the full recovery pipeline for one event."""
    event = db.get_event(event_id)
    if not event:
        return {"status": "ERROR", "reason": "Event not found"}

    if event["status"] in ("RECOVERED", "DEAD"):
        return {"status": "SKIPPED", "reason": f"Already {event['status']}"}

    t_fail = datetime.fromisoformat(event["failed_at"])
    t_now = datetime.utcnow()

    # ── Step 1: permanent failure → rail-swap ─────────────────────────
    if event["error_code"] in DEAD_ERROR_CODES:
        return _handle_dead_instrument(event)

    # ── Step 2: Hawkes scheduling ─────────────────────────────────────
    retry_dt, hazard, payroll = _hawkes.next_retry(t_fail, t_now)
    db.insert_hawkes_metric({
        "event_id": event_id,
        "computed_at": t_now.isoformat(),
        "hazard_rate": hazard,
        "next_retry_at": retry_dt.isoformat(),
        "payroll_score": payroll,
    })
    audit.log(
        event_id, "HAWKES_COMPUTED",
        f"h(t)={hazard}, next_retry={retry_dt.isoformat()}",
        hazard_rate=hazard, next_retry_at=retry_dt.isoformat(),
    )

    # ── Step 3: Prospect framing ──────────────────────────────────────
    frame = _framer.frame(event["category"], event["amount"], event["customer_name"])
    audit.log(
        event_id, "PROSPECT_FRAMED",
        f"frame={frame.frame_type}, discount={frame.discount_pct}%",
        framing=frame.frame_type, discount_pct=frame.discount_pct,
    )

    # ── Step 4: Guardrails ────────────────────────────────────────────
    gr = _guard.check_all(event, frame.discount_pct)
    if not gr.passed:
        audit.log(
            event_id, "GUARDRAIL_BLOCKED", gr.reason,
            guardrail_triggered=gr.guardrail_name,
        )
        db.update_event_status(event_id, "ESCALATED")
        return {
            "status": "ESCALATED",
            "reason": gr.reason,
            "guardrail": gr.guardrail_name,
        }

    # ── Step 5: create payment / affordability link ───────────────────
    link = _create_link(event, frame)
    audit.log(
        event_id, "RECOVERY_ATTEMPT",
        f"Link created: {link['short_url']}",
        link=link["short_url"],
        extra={"frame_type": frame.frame_type, "message": frame.message},
    )

    # ── Step 6: mock success check ────────────────────────────────────
    if link.get("success", False):
        db.update_event_status(event_id, "RECOVERED", datetime.utcnow().isoformat())
        audit.log(event_id, "RECOVERED", "Payment succeeded via recovery link")
        return {"status": "RECOVERED", "link": link["short_url"]}

    audit.log(event_id, "RETRY_PENDING", "Link sent, awaiting customer action")
    return {
        "status": "RETRY_PENDING",
        "next_retry_at": retry_dt.isoformat(),
        "link": link["short_url"],
        "frame": frame.frame_type,
        "message": frame.message,
    }


def _handle_dead_instrument(event: dict) -> dict:
    """Route dead instruments through rail-swap."""
    swap = generate_rail_swap_link(event)
    audit.log(
        event["event_id"], "RAIL_SWAP",
        f"Dead instrument ({event['error_code']}). Swap {swap['from_rail']}→{swap['to_rail']}",
        guardrail_triggered="DEAD_INSTRUMENT_BLOCK",
        link=swap["short_url"],
        extra={"swap_id": swap["swap_id"], "to_rail": swap["to_rail"]},
    )
    db.update_event_status(event["event_id"], "ESCALATED")
    return {
        "status": "ESCALATED",
        "reason": f"Rail-swap to {swap['to_rail']}",
        "swap_link": swap["short_url"],
    }


def _create_link(event: dict, frame) -> dict:
    """Pick payment or affordability link based on frame."""
    if frame.frame_type == "GAIN" and event["amount"] >= 2000:
        return create_affordability_link(
            event["amount"], event["customer_name"],
        )
    return create_payment_link(
        event["amount"], event["customer_name"],
        description=frame.message[:120],
    )


def run_batch(event_ids: Optional[list[str]] = None) -> list[dict]:
    """Run pipeline for all (or specified) pending events."""
    if event_ids is None:
        events = db.get_all_events()
        event_ids = [e["event_id"] for e in events if e["status"] == "PENDING"]
    results = []
    for eid in event_ids:
        result = run_recovery_pipeline(eid)
        result["event_id"] = eid
        results.append(result)
    return results
