"""Rule-based promise-to-pay parser — keyword + regex, no LLM."""

import re
from datetime import datetime, timedelta
from typing import Optional


# ── weekday map ───────────────────────────────────────────────────────

_WEEKDAYS = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

# ── compiled patterns ────────────────────────────────────────────────

_PAT_NTH = re.compile(
    r"\b(\d{1,2})\s*(?:st|nd|rd|th)\b", re.IGNORECASE
)
_PAT_NEXT_WEEK = re.compile(
    r"\bnext\s+week\b", re.IGNORECASE
)
_PAT_TOMORROW = re.compile(
    r"\btomorrow\b", re.IGNORECASE
)
_PAT_IN_DAYS = re.compile(
    r"\bin\s+(\d{1,2})\s+days?\b", re.IGNORECASE
)
_PAT_DATE_SLASH = re.compile(
    r"\b(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?\b"
)


def parse_promise(text: str, ref_date: Optional[datetime] = None) -> dict:
    """Extract a promised payment date from free-text customer message."""
    ref = ref_date or datetime.utcnow()
    text_lower = text.lower().strip()

    # ── "tomorrow" ────────────────────────────────────────────────────
    if _PAT_TOMORROW.search(text_lower):
        return _result(ref + timedelta(days=1), text, 0.95)

    # ── "in N days" ──────────────────────────────────────────────────
    m = _PAT_IN_DAYS.search(text_lower)
    if m:
        days = int(m.group(1))
        return _result(ref + timedelta(days=days), text, 0.90)

    # ── "next week" ──────────────────────────────────────────────────
    if _PAT_NEXT_WEEK.search(text_lower):
        days_ahead = 7 - ref.weekday()  # next Monday
        return _result(ref + timedelta(days=days_ahead), text, 0.75)

    # ── weekday name ("will pay Friday") ─────────────────────────────
    for name, idx in _WEEKDAYS.items():
        if name in text_lower:
            days_ahead = (idx - ref.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # same day ⇒ next week
            return _result(ref + timedelta(days=days_ahead), text, 0.85)

    # ── ordinal date ("on the 5th") ──────────────────────────────────
    m = _PAT_NTH.search(text_lower)
    if m:
        day = int(m.group(1))
        target = ref.replace(day=min(day, 28))
        if target <= ref:
            # next month
            month = ref.month % 12 + 1
            year = ref.year + (1 if month == 1 else 0)
            target = target.replace(month=month, year=year)
        return _result(target, text, 0.80)

    # ── explicit date (DD/MM or DD/MM/YYYY) ──────────────────────────
    m = _PAT_DATE_SLASH.search(text_lower)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else ref.year
        if year < 100:
            year += 2000
        try:
            target = datetime(year, month, day)
            return _result(target, text, 0.92)
        except ValueError:
            pass

    # ── no match ─────────────────────────────────────────────────────
    return {
        "promised_date": None,
        "raw_text": text,
        "confidence": 0.0,
        "parsed": False,
    }


def _result(dt: datetime, raw: str, confidence: float) -> dict:
    """Build a standard parse result dict."""
    return {
        "promised_date": dt.strftime("%Y-%m-%d"),
        "raw_text": raw,
        "confidence": confidence,
        "parsed": True,
    }
