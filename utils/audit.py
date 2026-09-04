"""Thin audit-log wrapper with consistent payload shape."""

from typing import Optional
from data.database import log_audit_entry


def log(
    event_id: str,
    action: str,
    reason: str,
    guardrail_triggered: Optional[str] = None,
    *,
    hazard_rate: Optional[float] = None,
    next_retry_at: Optional[str] = None,
    framing: Optional[str] = None,
    discount_pct: Optional[float] = None,
    link: Optional[str] = None,
    extra: Optional[dict] = None,
) -> None:
    """Write one immutable audit row with a normalized payload."""
    payload: dict = {}
    if hazard_rate is not None:
        payload["hazard_rate"] = hazard_rate
    if next_retry_at is not None:
        payload["next_retry_at"] = next_retry_at
    if framing is not None:
        payload["framing"] = framing
    if discount_pct is not None:
        payload["discount_pct"] = discount_pct
    if link is not None:
        payload["link"] = link
    if extra:
        payload.update(extra)
    log_audit_entry(
        event_id=event_id,
        action=action,
        reason=reason,
        guardrail_triggered=guardrail_triggered,
        payload=payload or None,
    )
