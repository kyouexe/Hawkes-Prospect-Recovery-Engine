# Hawkes-Prospect Recovery Engine

> **Razorpay Internship Submission** — Track 3: AI Revenue Recovery

A self-healing payment recovery system that combines **Hawkes point-process scheduling**
with **Prospect Theory framing** to optimally time and phrase recovery outreach for
failed payments.

---

## Problem Statement

Payment failures cost merchants revenue and create poor customer experiences. Current
retry logic uses fixed intervals that ignore:

1. **Temporal clustering** — bank outages cause correlated failures; retrying during an
   outage wastes attempts.
2. **Behavioural framing** — a SaaS subscriber about to lose access responds to
   different messaging than an e-commerce shopper who never received the item.
3. **Instrument death** — retrying an expired card or cancelled mandate is futile.

This engine addresses all three with mathematically grounded, auditable decisions.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard (app.py)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Pipeline │  │   P2P    │  │Analytics │  │  Audit Log    │  │
│  │   Tab    │  │ Sandbox  │  │   Tab    │  │    Tab        │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬───────┘  │
└───────┼──────────────┼────────────┼─────────────────┼──────────┘
        │              │            │                 │
        ▼              ▼            │                 │
┌───────────────────────────────────┼─────────────────┼──────────┐
│              engine/              │                 │          │
│  ┌──────────┐  ┌───────────┐     │                 │          │
│  │  Hawkes  │  │ Prospect  │     │                 │          │
│  │Scheduler │  │  Framer   │     │                 │          │
│  └────┬─────┘  └─────┬─────┘     │                 │          │
│       │              │           │                 │          │
│       ▼              ▼           │                 │          │
│  ┌──────────────────────────┐    │                 │          │
│  │     Guardrail Engine     │    │                 │          │
│  │  • 10% discount cap     │    │                 │          │
│  │  • 2 contacts/24h cap   │    │                 │          │
│  │  • Dead instrument block│    │                 │          │
│  └────────────┬─────────────┘    │                 │          │
│               │                  │                 │          │
│               ▼                  │                 │          │
│  ┌──────────────────────────┐    │                 │          │
│  │   Recovery Pipeline      │    │                 │          │
│  │  (orchestrates all)      │────┤                 │          │
│  └────────────┬─────────────┘    │                 │          │
└───────────────┼──────────────────┼─────────────────┼──────────┘
                │                  │                 │
        ┌───────┴───────┐         │                 │
        ▼               ▼         │                 │
┌──────────────┐ ┌────────────┐   │                 │
│ Razorpay Mock│ │ Rail Swap  │   │                 │
│ (Payment &   │ │ Service    │   │                 │
│  EMI Links)  │ │            │   │                 │
└──────────────┘ └────────────┘   │                 │
                                  │                 │
                    ┌─────────────┴─────────────────┘
                    ▼
           ┌─────────────────┐
           │   SQLite (WAL)  │
           │  • failure_events│
           │  • hawkes_metrics│
           │  • p2p_contracts │
           │  • audit_log     │
           └─────────────────┘
```

---

## How It Works

### 1. Hawkes Self-Exciting Process (WHEN to retry)

The hazard rate models temporal clustering of failures:

```
h(t) = μ₀ + α · exp(-β · (t - t₀)) + γ · payroll_score(t)
```

| Parameter | Meaning | Default |
|-----------|---------|---------|
| μ₀ | Baseline hazard rate | 0.3 |
| α | Excitation amplitude (recent cluster impact) | 0.8 |
| β | Decay rate (how fast cluster effect fades) | 0.5 |
| γ | Payroll cycle weight | 0.4 |

**Payroll score** returns 0.85–0.90 for dates 28th–5th (salary credit window)
and 0.15 for mid-month. This makes the engine prefer retries when customers
are most likely to have funds.

### 2. Prospect Theory (HOW to frame the offer)

| Customer Type | Frame | Psychology |
|--------------|-------|------------|
| SaaS / B2B Invoice | **Loss frame** | "Your access will be suspended in 48h" — leverages loss aversion |
| E-commerce | **Gain frame** | "Save ₹500 with EMI" — leverages aspirational gain |

### 3. Promise-to-Pay Parser

A rule-based (no LLM) regex engine that extracts dates from messages like:
- "I will pay on Friday" → next Friday, confidence 85%
- "Will transfer tomorrow" → tomorrow, confidence 95%
- "By the 5th" → 5th of current/next month, confidence 80%

### 4. Guardrails

| Rule | Limit | Action on Violation |
|------|-------|-------------------|
| Discount cap | ≤ 10% | Block and escalate |
| Contact cap | ≤ 2 per 24h | Block further contact |
| Dead instrument | EXPIRED_CARD, MANDATE_CANCELLED | Skip retry → rail-swap |

### 5. Rail Swap

Dead instruments are automatically offered an alternate payment rail:
- CARD / RUPAY → UPI AutoPay
- UPI AutoPay → eNACH
- eNACH → UPI AutoPay

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

The app uses a local SQLite database (`recovery.db`) that is auto-created on first
run with 20 seed failure events. Click **"Regenerate Seed Data"** in the sidebar
to reset.

---

## Tech Stack

- **Python 3.10+** with type hints
- **Streamlit** — interactive dashboard
- **Plotly** — funnel chart, hazard decay curves, framing scatter
- **SQLite** (WAL mode) — lightweight, zero-config persistence
- **No external APIs** — fully offline, mocked Razorpay responses

---

## Folder Structure

```
razorpay-recovery-engine/
├── app.py              # Streamlit UI
├── requirements.txt    # Dependencies
├── data/
│   ├── schema.py       # SQL table definitions
│   ├── seed_data.py    # 20 deterministic test events
│   └── database.py     # SQLite CRUD layer
├── engine/
│   ├── hawkes.py       # Hawkes point-process scheduler
│   ├── prospect.py     # Prospect Theory framer
│   ├── p2p_parser.py   # Promise-to-pay regex parser
│   ├── guardrails.py   # Discount / contact / instrument guards
│   └── pipeline.py     # Orchestration pipeline
├── services/
│   ├── razorpay_mock.py # Mocked payment link APIs
│   └── rail_swap.py     # Dead-instrument rail swap
└── utils/
    └── audit.py         # Audit log wrapper
```
