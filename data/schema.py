"""SQL schema constants for the recovery engine database."""

FAILURE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS failure_events (
    event_id TEXT PRIMARY KEY,
    customer_name TEXT,
    amount REAL,
    bank TEXT,
    instrument_type TEXT,
    error_code TEXT,
    category TEXT,
    failed_at TEXT,
    status TEXT,
    resolved_at TEXT
);
"""

HAWKES_METRICS_TABLE = """
CREATE TABLE IF NOT EXISTS hawkes_metrics (
    event_id TEXT,
    computed_at TEXT,
    hazard_rate REAL,
    next_retry_at TEXT,
    payroll_score REAL
);
"""

P2P_CONTRACTS_TABLE = """
CREATE TABLE IF NOT EXISTS p2p_contracts (
    contract_id TEXT PRIMARY KEY,
    event_id TEXT,
    promised_date TEXT,
    raw_customer_text TEXT,
    confidence REAL,
    status TEXT
);
"""

AUDIT_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    log_id TEXT PRIMARY KEY,
    event_id TEXT,
    timestamp TEXT,
    action TEXT,
    reason TEXT,
    guardrail_triggered TEXT,
    payload_json TEXT
);
"""

ALL_TABLES = [
    FAILURE_EVENTS_TABLE,
    HAWKES_METRICS_TABLE,
    P2P_CONTRACTS_TABLE,
    AUDIT_LOG_TABLE,
]
