"""Prospect Theory framing engine for recovery offers."""

from dataclasses import dataclass


@dataclass
class FrameResult:
    """Container for a framing decision."""
    frame_type: str       # LOSS or GAIN
    message: str
    discount_pct: float   # pre-guardrail suggestion


class ProspectFramer:
    """Decide loss- vs gain-framing and discount based on category + amount."""

    # ── thresholds ────────────────────────────────────────────────────

    LOSS_CATEGORIES = {"SAAS", "B2B_INVOICE"}
    GAIN_CATEGORIES = {"ECOMMERCE"}

    HIGH_VALUE_THRESHOLD = 5000.0  # ₹

    # ── public API ────────────────────────────────────────────────────

    def frame(self, category: str, amount: float, customer_name: str) -> FrameResult:
        """Return framed message + discount suggestion."""
        if category in self.LOSS_CATEGORIES:
            return self._loss_frame(category, amount, customer_name)
        return self._gain_frame(amount, customer_name)

    # ── private helpers ──────────────────────────────────────────────

    def _loss_frame(self, category: str, amount: float, name: str) -> FrameResult:
        """Loss-framing for SAAS / B2B — emphasise what customer loses."""
        discount = self._discount(amount)
        if category == "B2B_INVOICE":
            msg = (
                f"Hi {name}, your invoice payment of ₹{amount:,.0f} could not "
                f"be processed. Outstanding invoices may attract late-payment "
                f"penalties. Retry now to stay current."
            )
        else:
            msg = (
                f"Hi {name}, your subscription renewal of ₹{amount:,.0f} failed. "
                f"Your access will be suspended in 48 hours unless payment is "
                f"completed. Retry now to keep your service active."
            )
        return FrameResult(frame_type="LOSS", message=msg, discount_pct=discount)

    def _gain_frame(self, amount: float, name: str) -> FrameResult:
        """Gain-framing for ECOMMERCE — emphasise what customer gains."""
        discount = self._discount(amount)
        savings = amount * discount / 100
        msg = (
            f"Hi {name}, great news! Complete your purchase of ₹{amount:,.0f} "
            f"today and save ₹{savings:,.0f} with our recovery offer. "
            f"EMI options are also available at checkout."
        )
        return FrameResult(frame_type="GAIN", message=msg, discount_pct=discount)

    @staticmethod
    def _discount(amount: float) -> float:
        """Suggest pre-guardrail discount % based on amount tier."""
        if amount >= 50000:
            return 3.0
        if amount >= 10000:
            return 5.0
        if amount >= 2000:
            return 7.0
        return 10.0
