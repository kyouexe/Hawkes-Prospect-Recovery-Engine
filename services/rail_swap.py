"""Rail-swap service — convert dead instruments to alternate rails."""

import uuid


_SWAP_MAP = {
    "CARD": "UPI_AUTOPAY",
    "RUPAY": "UPI_AUTOPAY",
    "UPI_AUTOPAY": "ENACH",
    "ENACH": "UPI_AUTOPAY",
}


def generate_rail_swap_link(event: dict) -> dict:
    """Return a mocked rail-swap invitation payload."""
    current = event.get("instrument_type", "CARD")
    new_rail = _SWAP_MAP.get(current, "UPI_AUTOPAY")
    swap_id = f"swap_{uuid.uuid4().hex[:12]}"
    return {
        "swap_id": swap_id,
        "event_id": event["event_id"],
        "from_rail": current,
        "to_rail": new_rail,
        "short_url": f"https://rzp.io/swap/{swap_id[:8]}",
        "customer_name": event.get("customer_name", ""),
        "status": "INVITATION_SENT",
    }
