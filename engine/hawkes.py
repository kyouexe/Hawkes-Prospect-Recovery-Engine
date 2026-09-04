"""Hawkes self-exciting point-process scheduler for retry timing."""

import math
from datetime import datetime, timedelta
from typing import Optional


class HawkesScheduler:
    """Compute hazard rate h(t) and optimal next-retry time."""

    def __init__(
        self,
        mu0: float = 0.3,
        alpha: float = 0.8,
        beta: float = 0.5,
        gamma: float = 0.4,
    ) -> None:
        self.mu0 = mu0
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    # ── payroll score ─────────────────────────────────────────────────

    @staticmethod
    def payroll_score(dt: datetime) -> float:
        """Return 0.0–1.0 payroll-proximity score (28th–5th = high)."""
        day = dt.day
        if day >= 28 or day <= 5:
            return 0.85 + 0.05 * (1 if day <= 2 else 0)  # peak around 1st
        if 6 <= day <= 10:
            return 0.4  # tail
        return 0.15  # mid-month trough

    # ── hazard rate ───────────────────────────────────────────────────

    def hazard_rate(self, t_now: datetime, t_fail: datetime) -> float:
        """Compute h(t) = mu0 + alpha·exp(-beta·Δt) + gamma·payroll(t)."""
        delta_hours = max((t_now - t_fail).total_seconds() / 3600, 0.01)
        excitation = self.alpha * math.exp(-self.beta * delta_hours)
        payroll = self.gamma * self.payroll_score(t_now)
        return self.mu0 + excitation + payroll

    # ── next retry time ──────────────────────────────────────────────

    def next_retry(
        self,
        t_fail: datetime,
        t_now: Optional[datetime] = None,
    ) -> tuple[datetime, float, float]:
        """Return (next_retry_dt, hazard_rate, payroll_score)."""
        t_now = t_now or datetime.utcnow()
        h = self.hazard_rate(t_now, t_fail)
        # When h is high (recent cluster / bad payroll window), delay longer
        # When h is low (quiescent / good payroll window), retry sooner
        delay_hours = max(1.0, 24.0 * (1.0 - min(h, 1.5) / 1.5))
        retry_dt = t_now + timedelta(hours=delay_hours)
        ps = self.payroll_score(retry_dt)
        return retry_dt, round(h, 4), round(ps, 2)

    # ── decay curve for analytics ────────────────────────────────────

    def decay_curve(
        self,
        t_fail: datetime,
        hours: int = 72,
        steps: int = 100,
    ) -> list[dict]:
        """Return list of {hour, hazard_rate} for plotting h(t) decay."""
        points: list[dict] = []
        for i in range(steps + 1):
            offset = hours * i / steps
            t = t_fail + timedelta(hours=offset)
            h = self.hazard_rate(t, t_fail)
            points.append({"hour": round(offset, 2), "hazard_rate": round(h, 4)})
        return points
