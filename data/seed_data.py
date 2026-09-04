"""Deterministic seed data — 20 failure_event rows."""

from datetime import datetime, timedelta

_BASE = datetime(2026, 8, 25, 10, 0, 0)


def _ts(days: int, hours: int = 0) -> str:
    """Return ISO timestamp offset from _BASE."""
    return (_BASE + timedelta(days=days, hours=hours)).isoformat()


SEED_FAILURE_EVENTS: list[dict] = [
    # ── 6 × bank timeouts ─────────────────────────────────────────────
    {
        "event_id": "EVT001", "customer_name": "Aarav Mehta",
        "amount": 1499.0, "bank": "HDFC", "instrument_type": "UPI_AUTOPAY",
        "error_code": "TIMEOUT", "category": "SAAS",
        "failed_at": _ts(0, 9), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT002", "customer_name": "Priya Sharma",
        "amount": 2999.0, "bank": "SBI", "instrument_type": "ENACH",
        "error_code": "TIMEOUT", "category": "ECOMMERCE",
        "failed_at": _ts(1, 11), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT003", "customer_name": "Rohan Desai",
        "amount": 799.0, "bank": "ICICI", "instrument_type": "CARD",
        "error_code": "TIMEOUT", "category": "SAAS",
        "failed_at": _ts(2, 8), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT004", "customer_name": "Sneha Iyer",
        "amount": 4500.0, "bank": "HDFC", "instrument_type": "UPI_AUTOPAY",
        "error_code": "TIMEOUT", "category": "B2B_INVOICE",
        "failed_at": _ts(2, 14), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT005", "customer_name": "Vikram Joshi",
        "amount": 1200.0, "bank": "SBI", "instrument_type": "RUPAY",
        "error_code": "TIMEOUT", "category": "ECOMMERCE",
        "failed_at": _ts(3, 10), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT006", "customer_name": "Ananya Reddy",
        "amount": 3500.0, "bank": "ICICI", "instrument_type": "ENACH",
        "error_code": "TIMEOUT", "category": "SAAS",
        "failed_at": _ts(4, 16), "status": "PENDING", "resolved_at": None,
    },
    # ── 5 × expired cards ─────────────────────────────────────────────
    {
        "event_id": "EVT007", "customer_name": "Kavita Nair",
        "amount": 899.0, "bank": "HDFC", "instrument_type": "CARD",
        "error_code": "EXPIRED_CARD", "category": "ECOMMERCE",
        "failed_at": _ts(1, 7), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT008", "customer_name": "Arjun Pillai",
        "amount": 5999.0, "bank": "AXIS", "instrument_type": "CARD",
        "error_code": "EXPIRED_CARD", "category": "SAAS",
        "failed_at": _ts(2, 12), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT009", "customer_name": "Deepa Kulkarni",
        "amount": 1599.0, "bank": "SBI", "instrument_type": "CARD",
        "error_code": "EXPIRED_CARD", "category": "ECOMMERCE",
        "failed_at": _ts(3, 9), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT010", "customer_name": "Manish Gupta",
        "amount": 2499.0, "bank": "ICICI", "instrument_type": "CARD",
        "error_code": "EXPIRED_CARD", "category": "SAAS",
        "failed_at": _ts(5, 15), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT011", "customer_name": "Neha Verma",
        "amount": 749.0, "bank": "HDFC", "instrument_type": "RUPAY",
        "error_code": "EXPIRED_CARD", "category": "ECOMMERCE",
        "failed_at": _ts(6, 11), "status": "PENDING", "resolved_at": None,
    },
    # ── 4 × cancelled mandates ────────────────────────────────────────
    {
        "event_id": "EVT012", "customer_name": "Siddharth Rao",
        "amount": 999.0, "bank": "HDFC", "instrument_type": "UPI_AUTOPAY",
        "error_code": "MANDATE_CANCELLED", "category": "SAAS",
        "failed_at": _ts(3, 13), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT013", "customer_name": "Pooja Bhat",
        "amount": 1799.0, "bank": "SBI", "instrument_type": "ENACH",
        "error_code": "MANDATE_CANCELLED", "category": "SAAS",
        "failed_at": _ts(4, 8), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT014", "customer_name": "Rajesh Kumar",
        "amount": 3200.0, "bank": "ICICI", "instrument_type": "UPI_AUTOPAY",
        "error_code": "MANDATE_CANCELLED", "category": "ECOMMERCE",
        "failed_at": _ts(5, 10), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT015", "customer_name": "Lakshmi Menon",
        "amount": 2100.0, "bank": "AXIS", "instrument_type": "ENACH",
        "error_code": "MANDATE_CANCELLED", "category": "SAAS",
        "failed_at": _ts(7, 14), "status": "PENDING", "resolved_at": None,
    },
    # ── 5 × high-value B2B insufficient funds ────────────────────────
    {
        "event_id": "EVT016", "customer_name": "Amit Patel",
        "amount": 45000.0, "bank": "HDFC", "instrument_type": "ENACH",
        "error_code": "INSUFFICIENT_FUNDS", "category": "B2B_INVOICE",
        "failed_at": _ts(4, 9), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT017", "customer_name": "Sunita Agarwal",
        "amount": 85000.0, "bank": "SBI", "instrument_type": "CARD",
        "error_code": "INSUFFICIENT_FUNDS", "category": "B2B_INVOICE",
        "failed_at": _ts(5, 11), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT018", "customer_name": "Karthik Rangan",
        "amount": 12500.0, "bank": "ICICI", "instrument_type": "UPI_AUTOPAY",
        "error_code": "INSUFFICIENT_FUNDS", "category": "B2B_INVOICE",
        "failed_at": _ts(6, 14), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT019", "customer_name": "Divya Saxena",
        "amount": 67000.0, "bank": "AXIS", "instrument_type": "ENACH",
        "error_code": "INSUFFICIENT_FUNDS", "category": "B2B_INVOICE",
        "failed_at": _ts(8, 10), "status": "PENDING", "resolved_at": None,
    },
    {
        "event_id": "EVT020", "customer_name": "Rahul Banerjee",
        "amount": 23000.0, "bank": "HDFC", "instrument_type": "CARD",
        "error_code": "INSUFFICIENT_FUNDS", "category": "B2B_INVOICE",
        "failed_at": _ts(9, 16), "status": "PENDING", "resolved_at": None,
    },
]
