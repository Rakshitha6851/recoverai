"""
RecoverAI backend.

Detect -> Diagnose -> Decide -> Recover -> Audit

Design note (read this before changing the policy):
All revenue numbers in this file (the /metrics dashboard cards AND the
/strategy-comparison batch comparison) are computed from the SAME two
sources of truth:

  1. data/payments.csv            -> which payments failed, why, attempt #
  2. data/historical_outcomes.csv -> whether that payment was actually
                                      recovered, and for how much

There is no randomised / re-simulated recovery anywhere in this file.
Earlier versions of this project simulated "success" with
`random.seed(...)` + a hand-picked probability per action, which produced
numbers that quietly disagreed with the README and with each other. That
has been removed. If you regenerate the CSVs (see data/generate_data.py,
data/historical_outcomes.py, data/generate_audit.py) the numbers here will
change accordingly, but /metrics and /strategy-comparison will always
agree with each other because they share the `recoverai_decision()` /
`batch_summary()` helpers below.
"""

import hashlib

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd


app = FastAPI(title="RecoverAI")


PAYMENTS_FILE = "data/payments.csv"
OUTCOMES_FILE = "data/historical_outcomes.csv"
AUDIT_FILE = "data/audit_trail.csv"

MAX_ATTEMPTS = 3

# Reasons RecoverAI will attempt an automatic RETRY for.
AUTO_RETRY_REASONS = ["timeout", "network_error", "bank_error"]

# Reasons that require the customer to act (never blindly retried).
CUSTOMER_ACTION_REASONS = ["insufficient_funds", "limit_exceeded"]

# Reasons that require re-authentication.
AUTH_REASONS = ["authentication_failed"]

# --- Naive-strategy counterfactual assumption (disclosed) ---
# A blind retry is the CORRECT fix for a technical failure (timeout,
# network error, bank error) -- retrying again genuinely can succeed.
# It is NOT the correct fix for a customer-controlled failure: retrying
# an insufficient-funds or wrong-authentication payment with no change
# does not address the underlying problem. A blind retry only recovers
# a fraction of those cases (e.g. the customer happened to top up their
# account in the meantime), which we model as a fixed effectiveness
# multiplier below. These numbers are a disclosed modelling assumption,
# not a fitted result -- they exist so the naive-vs-RecoverAI comparison
# reflects *why* targeted routing helps, instead of crediting a blind
# retry with the same success rate as the correct action.
NAIVE_RETRY_EFFECTIVENESS = {
    "timeout": 1.0,
    "network_error": 1.0,
    "bank_error": 1.0,
    "insufficient_funds": 0.35,
    "limit_exceeded": 0.35,
    "authentication_failed": 0.20,
}


def _deterministic_unit_interval(payment_id: str) -> float:
    """
    Deterministic, reproducible pseudo-random number in [0, 1) derived
    from the payment_id. Used only for the naive-strategy counterfactual
    above -- NOT used anywhere in the RecoverAI decision or outcome path,
    which always uses the real recorded historical outcome.
    """
    digest = hashlib.sha256(payment_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


class Payment(BaseModel):
    payment_id: str
    amount: float
    status: str
    failure_reason: str | None = None


def recoverai_decision(row) -> str:
    """
    The RecoverAI recovery policy.

    This is intentionally a small, auditable rule set rather than an
    opaque ML prediction -- see README "Why rules, not ML" for the
    reasoning. It is the ONLY place this decision logic lives; every
    endpoint below calls this function so the policy can never drift
    between endpoints.
    """
    reason = row["failure_reason"]
    attempts = row["attempt_number"]

    # Hard safety gate: never retry a payment more than MAX_ATTEMPTS times.
    if attempts >= MAX_ATTEMPTS:
        return "STOP_AND_ESCALATE"

    if reason in AUTO_RETRY_REASONS:
        return "RETRY_PAYMENT"

    if reason in CUSTOMER_ACTION_REASONS:
        return "CUSTOMER_ACTION_REQUIRED"

    if reason in AUTH_REASONS:
        return "CUSTOMER_AUTHENTICATION_REQUIRED"

    return "MANUAL_REVIEW"


def load_failed_with_outcomes() -> pd.DataFrame:
    """
    Join failed payments with their real historical outcome
    (recovered / recovered_amount) and attach the RecoverAI decision.
    """
    try:
        payments = pd.read_csv(PAYMENTS_FILE)
        outcomes = pd.read_csv(OUTCOMES_FILE)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Required data files not found",
        )

    failed = payments[payments["status"] == "failed"].copy()

    failed = failed.merge(
        outcomes[["payment_id", "recovered", "recovered_amount"]],
        on="payment_id",
        how="left",
    )

    # A failed payment with no matching historical outcome row is
    # treated as "not recovered" rather than silently dropped.
    failed["recovered"] = failed["recovered"].fillna(False).astype(bool)
    failed["recovered_amount"] = failed["recovered_amount"].fillna(0.0)

    failed["recommended_action"] = failed.apply(recoverai_decision, axis=1)

    return failed


def batch_summary(failed: pd.DataFrame) -> dict:
    """
    Compare a naive "retry everything under 3 attempts" strategy against
    RecoverAI's policy.

    RecoverAI's numbers come directly from the real recorded outcome in
    historical_outcomes.csv -- no simulation.

    The naive strategy also starts from that same real outcome, but a
    payment only counts as "recovered by naive retry" if (a) it was
    actually recovered, AND (b) a blind retry would plausibly have been
    the thing that recovered it -- see NAIVE_RETRY_EFFECTIVENESS above.
    For technical failures this is always true (retry is the correct
    fix either way). For customer-controlled failures it is only true
    some of the time, because blindly retrying doesn't address the
    actual problem.
    """
    total_at_risk = float(failed["amount"].sum())

    # --- Naive strategy: blindly retry every failed payment with
    #     attempt_number < 3, regardless of why it failed. ---
    naive = failed[failed["attempt_number"] < MAX_ATTEMPTS].copy()

    def naive_would_recover(row) -> bool:
        if not row["recovered"]:
            return False
        effectiveness = NAIVE_RETRY_EFFECTIVENESS.get(
            row["failure_reason"], 1.0
        )
        return _deterministic_unit_interval(row["payment_id"]) < effectiveness

    naive["naive_recovered"] = naive.apply(naive_would_recover, axis=1)
    naive["naive_recovered_amount"] = naive["amount"].where(
        naive["naive_recovered"], 0.0
    )

    naive_attempted = int(len(naive))
    naive_recovered_count = int(naive["naive_recovered"].sum())
    naive_revenue_recovered = float(naive["naive_recovered_amount"].sum())

    # --- RecoverAI strategy: only take an active recovery action
    #     (retry, customer action, or authentication) when the policy
    #     says to. Escalated payments get no automatic action, so no
    #     automatic recovery credit. ---
    active_actions = [
        "RETRY_PAYMENT",
        "CUSTOMER_ACTION_REQUIRED",
        "CUSTOMER_AUTHENTICATION_REQUIRED",
    ]
    ai_active = failed[failed["recommended_action"].isin(active_actions)]

    ai_attempted = int(
        (failed["recommended_action"] == "RETRY_PAYMENT").sum()
    )
    ai_recovered_count = int(ai_active["recovered"].sum())
    ai_revenue_recovered = float(ai_active["recovered_amount"].sum())

    return {
        "total_failed_payments": int(len(failed)),
        "total_revenue_at_risk": total_at_risk,
        "naive": {
            "payments_attempted": naive_attempted,
            "payments_recovered": naive_recovered_count,
            "revenue_recovered": naive_revenue_recovered,
        },
        "recoverai": {
            "payments_attempted": ai_attempted,
            "payments_recovered": ai_recovered_count,
            "revenue_recovered": ai_revenue_recovered,
        },
        "impact": {
            "additional_revenue_recovered": (
                ai_revenue_recovered - naive_revenue_recovered
            ),
            "retries_reduced": naive_attempted - ai_attempted,
        },
        "stopping_rule": (
            "RecoverAI does not retry payments with 3 or more "
            "previous attempts, and does not blindly retry "
            "customer-controlled failures (insufficient funds, "
            "limit exceeded, authentication failed)."
        ),
    }


@app.get("/")
def home():
    return {
        "message": "RecoverAI is running!",
        "project": "AI Failed Payment Recovery Agent",
    }


@app.post("/payments")
def create_payment(payment: Payment):
    return {
        "message": "Payment received",
        "payment": payment,
    }


@app.get("/dashboard")
def dashboard():
    return FileResponse("frontend/index.html")


@app.get("/payments/{payment_id}")
def get_recovery_decision(payment_id: str):
    try:
        df = pd.read_csv(AUDIT_FILE)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Audit trail not found",
        )

    result = df[df["payment_id"] == payment_id]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    row = result.iloc[0]

    return {
        "payment_id": row["payment_id"],
        "amount": float(row["amount"]),
        "failure_reason": row["failure_reason"],
        "attempt_number": int(row["attempt_number"]),
        "recommended_action": row["recommended_action"],
        "decision_reason": row["decision_reason"],
        "expected_recovery_value": float(row["expected_recovery_value"]),
        "stopping_rule": (
            f"Maximum {MAX_ATTEMPTS} attempts; "
            f"escalate after {MAX_ATTEMPTS} attempts"
        ),
        "audit_status": row["audit_status"],
    }


@app.post("/payments/{payment_id}/recover")
def recover_payment(payment_id: str):
    """
    Execute the bounded recovery workflow for one payment.

    IMPORTANT (simulation disclosure): this buildathon build does not call
    a live payment gateway. It replays the pre-computed historical outcome
    for that payment_id from data/historical_outcomes.csv, which was
    generated with a fixed, disclosed probability per failure reason (see
    data/historical_outcomes.py). This lets the safety rules, decision
    logic, and audit trail be demonstrated end-to-end without needing a
    live sandbox. Swapping in a real gateway call would only require
    replacing the lookup below with an actual retry/notify API call.
    """
    try:
        audit_df = pd.read_csv(AUDIT_FILE)
        history_df = pd.read_csv(OUTCOMES_FILE)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Recovery data not available",
        )

    payment = audit_df[audit_df["payment_id"] == payment_id]

    if payment.empty:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    payment = payment.iloc[0]
    attempt_number = int(payment["attempt_number"])

    # HARD STOP: safety gate, independent of everything else below.
    if attempt_number >= MAX_ATTEMPTS:
        return {
            "payment_id": payment_id,
            "recovery_attempted": False,
            "recovered": False,
            "recovered_amount": 0.0,
            "message": "Maximum retry attempts reached. Escalation required.",
            "audit_status": "ESCALATION_REQUIRED",
            "stopping_rule": f"Maximum {MAX_ATTEMPTS} attempts",
        }

    # Only fully-automatic retries are executed here. Customer-action and
    # authentication cases are routed to the customer, not retried.
    if payment["recommended_action"] != "RETRY_PAYMENT":
        return {
            "payment_id": payment_id,
            "recovery_attempted": False,
            "recovered": False,
            "recovered_amount": 0.0,
            "message": "Automatic recovery not appropriate.",
            "audit_status": "CUSTOMER_ACTION_REQUIRED",
            "stopping_rule": "No automatic retry for customer-controlled failures",
        }

    historical = history_df[history_df["payment_id"] == payment_id]

    if historical.empty:
        recovered = False
        recovered_amount = 0.0
    else:
        historical = historical.iloc[0]
        recovered = bool(historical["recovered"])
        recovered_amount = (
            float(historical["recovered_amount"]) if recovered else 0.0
        )

    return {
        "payment_id": payment_id,
        "recovery_attempted": True,
        "recovered": recovered,
        "recovered_amount": recovered_amount,
        "message": (
            "Payment recovered successfully"
            if recovered
            else "Recovery attempt unsuccessful"
        ),
        "audit_status": (
            "RECOVERY_RECORDED" if recovered else "RECOVERY_FAILED"
        ),
        "stopping_rule": f"Maximum {MAX_ATTEMPTS} attempts",
    }


@app.get("/metrics")
def get_metrics():
    failed = load_failed_with_outcomes()

    revenue_at_risk = float(failed["amount"].sum())
    revenue_recovered = float(failed["recovered_amount"].sum())
    recovery_rate = (
        revenue_recovered / revenue_at_risk * 100 if revenue_at_risk > 0 else 0
    )

    summary = batch_summary(failed)

    return {
        "failed_payments": int(len(failed)),
        "revenue_at_risk": revenue_at_risk,
        "revenue_recovered": revenue_recovered,
        "recovery_rate": round(recovery_rate, 2),
        "naive_revenue_recovered": summary["naive"]["revenue_recovered"],
        "recoverai_revenue_recovered": summary["recoverai"]["revenue_recovered"],
        "additional_revenue": summary["impact"]["additional_revenue_recovered"],
        "retries_reduced": summary["impact"]["retries_reduced"],
    }


@app.get("/strategy-comparison")
def strategy_comparison():
    failed = load_failed_with_outcomes()
    return batch_summary(failed)
