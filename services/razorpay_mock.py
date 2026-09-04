"""Mocked Razorpay API — no network calls, no SDK dependency."""

import uuid
import random


def create_payment_link(
    amount: float,
    customer_name: str,
    description: str = "",
) -> dict:
    """Return a fake Razorpay payment link payload."""
    link_id = f"plink_{uuid.uuid4().hex[:14]}"
    return {
        "id": link_id,
        "amount": int(amount * 100),  # paise
        "currency": "INR",
        "short_url": f"https://rzp.io/i/{link_id[:8]}",
        "customer_name": customer_name,
        "description": description,
        "status": "created",
        "success": random.random() < 0.65,  # 65% mock success rate
    }


def create_affordability_link(
    amount: float,
    customer_name: str,
    emi_months: int = 3,
) -> dict:
    """Return a fake EMI / affordability widget link."""
    widget_id = f"aff_{uuid.uuid4().hex[:12]}"
    monthly = round(amount / emi_months, 2)
    return {
        "id": widget_id,
        "short_url": f"https://rzp.io/emi/{widget_id[:8]}",
        "emi_months": emi_months,
        "monthly_amount": monthly,
        "customer_name": customer_name,
        "status": "created",
    }
