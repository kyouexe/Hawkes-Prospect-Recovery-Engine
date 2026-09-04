"""Guardrail engine — discount cap, contact cap, dead-instrument block."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from data.database import get_audit_log


# ── constants ─────────────────────────────────────────────────────────

MAX_DISCOUNT_PCT = 10.0
MAX_CONTACTS_24H = 2
DEAD_ERROR_CODES = {"EXPIRED_CARD", "MANDATE_CANCELLED"}


@dataclass
class GuardrailResult:
    """Outcome of a guardrail check."""
    passed: bool
    reason: str
    guardrail_name: Optional[str] = None  # set when blocked


class GuardrailEngine:
    """Enforce risk guardrails before any recovery action proceeds."""

    def check_all(
        self,
        event: dict,
        proposed_discount: float,
    ) -> GuardrailResult:
        """Run all guardrails in priority order, fail-fast."""
        checks = [
            self._dead_instrument(event),
            self._discount_cap(proposed_discount),
            self._contact_cap(event["event_id"]),
        ]
        for result in checks:
            if not result.passed:
                return result
        return GuardrailResult(passed=True, reason="All guardrails passed")

    # ── individual checks ────────────────────────────────────────────

    def _dead_instrument(self, event: dict) -> GuardrailResult:
        """Block retry on permanently-failed instruments."""
        if event.get("error_code") in DEAD_ERROR_CODES:
            return GuardrailResult(
                passed=False,
                reason=f"Instrument dead: {event['error_code']}. Route to rail-swap.",
                guardrail_name="DEAD_INSTRUMENT_BLOCK",
            )
        return GuardrailResult(passed=True, reason="Instrument alive")

    def _discount_cap(self, pct: float) -> GuardrailResult:
        """Enforce ≤10% discount ceiling."""
        if pct > MAX_DISCOUNT_PCT:
            return GuardrailResult(
                passed=False,
                reason=f"Discount {pct}% exceeds cap of {MAX_DISCOUNT_PCT}%",
                guardrail_name="DISCOUNT_CAP",
            )
        return GuardrailResult(passed=True, reason="Discount within cap")

    def _contact_cap(self, event_id: str) -> GuardrailResult:
        """Limit to 2 contact attempts in trailing 24 h."""
        logs = get_audit_log(event_id=event_id)
        now = datetime.utcnow()
        recent = 0
        for row in logs:
            if row.get("action") in ("CONTACT_SENT", "RECOVERY_ATTEMPT"):
                ts = datetime.fromisoformat(row["timestamp"])
                if (now - ts).total_seconds() < 86400:
                    recent += 1
        if recent >= MAX_CONTACTS_24H:
            return GuardrailResult(
                passed=False,
                reason=f"Contact cap reached ({recent}/{MAX_CONTACTS_24H} in 24h)",
                guardrail_name="CONTACT_CAP_24H",
            )
        return GuardrailResult(passed=True, reason="Contact cap OK")
