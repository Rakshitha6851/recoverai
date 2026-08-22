from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd


app = FastAPI(title="RecoverAI")


AUDIT_FILE = "data/audit_trail.csv"


class Payment(BaseModel):
    payment_id: str
    amount: float
    status: str
    failure_reason: str | None = None


@app.get("/")
def home():
    return {
        "message": "RecoverAI is running!",
        "project": "AI Failed Payment Recovery Agent"
    }


@app.post("/payments")
def create_payment(payment: Payment):
    return {
        "message": "Payment received",
        "payment": payment
    }


@app.get("/payments/{payment_id}")
def get_recovery_decision(payment_id: str):

    try:
        df = pd.read_csv(AUDIT_FILE)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Audit trail not found"
        )

    result = df[
        df["payment_id"] == payment_id
    ]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    row = result.iloc[0]

    return {
        "payment_id": row["payment_id"],
        "amount": float(row["amount"]),
        "failure_reason": row["failure_reason"],
        "attempt_number": int(row["attempt_number"]),
        "recommended_action": row["recommended_action"],
        "decision_reason": row["decision_reason"],
        "expected_recovery_value": float(
            row["expected_recovery_value"]
        ),
        "stopping_rule": (
            "Maximum 3 attempts; "
            "escalate after 3 attempts"
        ),
        "audit_status": row["audit_status"]
    }
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd


app = FastAPI(title="RecoverAI")


AUDIT_FILE = "data/audit_trail.csv"


class Payment(BaseModel):
    payment_id: str
    amount: float
    status: str
    failure_reason: str | None = None


@app.get("/")
def home():
    return {
        "message": "RecoverAI is running!",
        "project": "AI Failed Payment Recovery Agent"
    }


@app.post("/payments")
def create_payment(payment: Payment):
    return {
        "message": "Payment received",
        "payment": payment
    }


@app.get("/payments/{payment_id}")
def get_recovery_decision(payment_id: str):

    try:
        df = pd.read_csv(AUDIT_FILE)
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Audit trail not found"
        )

    result = df[
        df["payment_id"] == payment_id
    ]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    row = result.iloc[0]

    return {
        "payment_id": row["payment_id"],
        "amount": float(row["amount"]),
        "failure_reason": row["failure_reason"],
        "attempt_number": int(row["attempt_number"]),
        "recommended_action": row["recommended_action"],
        "decision_reason": row["decision_reason"],
        "expected_recovery_value": float(
            row["expected_recovery_value"]
        ),
        "stopping_rule": (
            "Maximum 3 attempts; "
            "escalate after 3 attempts"
        ),
        "audit_status": row["audit_status"]
    }
@app.get("/dashboard")
def dashboard():
    return FileResponse("frontend/index.html")
@app.get("/metrics")
def get_metrics():

    try:
        payments = pd.read_csv("data/payments.csv")
        outcomes = pd.read_csv("data/historical_outcomes.csv")
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Required data files not found"
        )

    failed = payments[
        payments["status"] == "failed"
    ].copy()

    failed_payments = len(failed)

    revenue_at_risk = failed["amount"].sum()

    revenue_recovered = outcomes[
        outcomes["recovered"] == True
    ]["recovered_amount"].sum()

    recovery_rate = (
        revenue_recovered / revenue_at_risk * 100
        if revenue_at_risk > 0
        else 0
    )

    # -------------------------------
    # BATCH STRATEGY COMPARISON
    # -------------------------------

    # Naive strategy:
    # retry every failed payment with fewer than 3 attempts
    naive = failed[
        failed["attempt_number"] < 3
    ].copy()

    naive["recovered"] = (
        outcomes.loc[
            outcomes["payment_id"].isin(
                naive["payment_id"]
            ),
            "recovered"
        ].values
    )

    naive_revenue_recovered = naive[
        naive["recovered"] == True
    ]["amount"].sum()

    naive_attempted = len(naive)

    # RecoverAI strategy
    def recoverai_decision(row):

        reason = row["failure_reason"]
        attempts = row["attempt_number"]

        if attempts >= 3:
            return "STOP_AND_ESCALATE"

        if reason in [
            "timeout",
            "network_error",
            "bank_error"
        ]:
            return "RETRY_PAYMENT"

        if reason in [
            "insufficient_funds",
            "limit_exceeded"
        ]:
            return "CUSTOMER_ACTION_REQUIRED"

        if reason == "authentication_failed":
            return "CUSTOMER_AUTHENTICATION_REQUIRED"

        return "MANUAL_REVIEW"

    failed["recommended_action"] = failed.apply(
        recoverai_decision,
        axis=1
    )

    ai_attempted = (
        failed["recommended_action"]
        == "RETRY_PAYMENT"
    ).sum()

    ai_recovered = outcomes[
        outcomes["recovered"] == True
    ]

    ai_revenue_recovered = ai_recovered[
        ai_recovered["payment_id"].isin(
            failed[
                failed["recommended_action"]
                == "RETRY_PAYMENT"
            ]["payment_id"]
        )
    ]["recovered_amount"].sum()

    additional_revenue = (
        ai_revenue_recovered
        - naive_revenue_recovered
    )

    retries_reduced = (
        naive_attempted
        - ai_attempted
    )

    return {
        "failed_payments": int(failed_payments),

        "revenue_at_risk":
            float(revenue_at_risk),

        "revenue_recovered":
            float(revenue_recovered),

        "recovery_rate":
            round(recovery_rate, 2),

        "naive_revenue_recovered":
            float(naive_revenue_recovered),

        "recoverai_revenue_recovered":
            float(ai_revenue_recovered),

        "additional_revenue":
            float(additional_revenue),

        "retries_reduced":
            int(retries_reduced)
    }
@app.post("/payments/{payment_id}/recover")
def recover_payment(payment_id: str):

    import pandas as pd
    from fastapi import HTTPException

    try:
        audit_df = pd.read_csv("data/audit_trail.csv")
        history_df = pd.read_csv("data/historical_outcomes.csv")
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Recovery data not available"
        )

    payment = audit_df[
        audit_df["payment_id"] == payment_id
    ]

    if payment.empty:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    payment = payment.iloc[0]

    attempt_number = int(payment["attempt_number"])

    # HARD STOP
    if attempt_number >= 3:
        return {
            "payment_id": payment_id,
            "recovery_attempted": False,
            "recovered": False,
            "recovered_amount": 0.0,
            "message": "Maximum retry attempts reached. Escalation required.",
            "audit_status": "ESCALATION_REQUIRED",
            "stopping_rule": "Maximum 3 attempts"
        }

    # Only retry payments recommended by RecoverAI
    if payment["recommended_action"] != "RETRY_PAYMENT":
        return {
            "payment_id": payment_id,
            "recovery_attempted": False,
            "recovered": False,
            "recovered_amount": 0.0,
            "message": "Automatic recovery not appropriate.",
            "audit_status": "CUSTOMER_ACTION_REQUIRED",
            "stopping_rule": "No automatic retry for customer-controlled failures"
        }

    # Find historical outcome for this payment
    historical = history_df[
        history_df["payment_id"] == payment_id
    ]

    if historical.empty:
        recovered = False
        recovered_amount = 0.0
    else:
        historical = historical.iloc[0]

        recovered = bool(historical["recovered"])

        recovered_amount = (
            float(historical["recovered_amount"])
            if recovered
            else 0.0
        )

    return {
        "payment_id": payment_id,
        "recovery_attempted": True,
        "recovered": recovered,
        "recovered_amount": recovered_amount,
        "message":
            "Payment recovered successfully"
            if recovered
            else "Recovery attempt unsuccessful",
        "audit_status": 
             "RECOVERY_RECORDED"
             if recovered
             else "RECOVERY_FAILED",
        "stopping_rule": "Maximum 3 attempts"
    }
@app.get("/strategy-comparison")
def strategy_comparison():

    import pandas as pd
    import random

    try:
        df = pd.read_csv("data/payments.csv")
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Payments data not found"
        )

    failed = df[df["status"] == "failed"].copy()

    # -------------------------------
    # NAIVE RETRY
    # -------------------------------

    naive = failed[
        failed["attempt_number"] < 3
    ].copy()

    naive_recovered = 0.0
    naive_recovered_count = 0

    for index, row in naive.iterrows():

        random.seed(42 + index)

        if random.random() < 0.40:
            naive_recovered += float(row["amount"])
            naive_recovered_count += 1

    naive_attempted = len(naive)

    # -------------------------------
    # RECOVERAI
    # -------------------------------

    def recoverai_decision(row):

        reason = row["failure_reason"]
        attempts = row["attempt_number"]

        if attempts >= 3:
            return "STOP_AND_ESCALATE"

        if reason in [
            "timeout",
            "network_error",
            "bank_error"
        ]:
            return "RETRY_PAYMENT"

        if reason in [
            "insufficient_funds",
            "limit_exceeded"
        ]:
            return "CUSTOMER_ACTION_REQUIRED"

        if reason == "authentication_failed":
            return "CUSTOMER_AUTHENTICATION_REQUIRED"

        return "MANUAL_REVIEW"

    ai = failed.copy()

    ai["recommended_action"] = ai.apply(
        recoverai_decision,
        axis=1
    )

    ai_recovered = 0.0
    ai_recovered_count = 0

    for index, row in ai.iterrows():

        action = row["recommended_action"]

        probabilities = {
            "RETRY_PAYMENT": 0.60,
            "CUSTOMER_ACTION_REQUIRED": 0.35,
            "CUSTOMER_AUTHENTICATION_REQUIRED": 0.30,
            "STOP_AND_ESCALATE": 0.00
        }

        probability = probabilities.get(
            action,
            0.0
        )

        random.seed(1000 + index)

        if random.random() < probability:
            ai_recovered += float(row["amount"])
            ai_recovered_count += 1

    ai_attempted = (
        ai["recommended_action"]
        == "RETRY_PAYMENT"
    ).sum()

    total_at_risk = failed["amount"].sum()

    additional_revenue = (
        ai_recovered - naive_recovered
    )

    retries_reduced = (
        naive_attempted - ai_attempted
    )

    return {
        "total_failed_payments": int(len(failed)),

        "total_revenue_at_risk":
            float(total_at_risk),

        "naive": {
            "payments_attempted":
                int(naive_attempted),
            "payments_recovered":
                int(naive_recovered_count),
            "revenue_recovered":
                float(naive_recovered)
        },

        "recoverai": {
            "payments_attempted":
                int(ai_attempted),
            "payments_recovered":
                int(ai_recovered_count),
            "revenue_recovered":
                float(ai_recovered)
        },

        "impact": {
            "additional_revenue_recovered":
                float(additional_revenue),
            "retries_reduced":
                int(retries_reduced)
        },

        "stopping_rule":
            "RecoverAI does not retry payments with 3 or more previous attempts."
    }