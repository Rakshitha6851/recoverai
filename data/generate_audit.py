import pandas as pd


INPUT_FILE = "data/historical_outcomes.csv"
OUTPUT_FILE = "data/audit_trail.csv"


RECOVERY_PROBABILITY = {
    "timeout": 0.65,
    "network_error": 0.60,
    "bank_error": 0.55,
    "insufficient_funds": 0.35,
    "limit_exceeded": 0.30,
    "authentication_failed": 0.25,
}


def decide(row):

    reason = row["failure_reason"]
    amount = row["amount"]
    attempts = row["attempt_number"]

    probability = RECOVERY_PROBABILITY[reason]

    expected_recovery = amount * probability

    if attempts >= 3:
        return (
            "ESCALATE",
            "Stopping rule triggered: "
            "3 or more previous attempts"
        )

    if reason in [
        "timeout",
        "network_error",
        "bank_error",
    ]:
        return (
            "RETRY_PAYMENT",
            "Temporary technical failure; "
            "bounded retry is appropriate"
        )

    if reason in [
        "insufficient_funds",
        "limit_exceeded",
    ]:
        return (
            "CUSTOMER_ACTION",
            "Customer-controlled payment issue; "
            "customer intervention required"
        )

    if reason == "authentication_failed":
        return (
            "AUTHENTICATION",
            "Payment authentication is required"
        )

    return (
        "ESCALATE",
        "No safe automated recovery action"
    )


def main():

    df = pd.read_csv(INPUT_FILE)

    decisions = df.apply(
        decide,
        axis=1,
        result_type="expand"
    )

    df["recommended_action"] = decisions[0]
    df["decision_reason"] = decisions[1]

    df["expected_recovery_value"] = (
        df["amount"]
        * df["failure_reason"].map(
            RECOVERY_PROBABILITY
        )
    )

    df["audit_status"] = "DECISION_RECORDED"

    audit_columns = [
        "payment_id",
        "amount",
        "failure_reason",
        "attempt_number",
        "recommended_action",
        "decision_reason",
        "expected_recovery_value",
        "audit_status",
    ]

    audit = df[audit_columns]

    audit.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("========== RecoverAI Audit Trail ==========")

    print(
        f"Audit records created: "
        f"{len(audit):,}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print("\nSample audit records:")

    print(
        audit.head(10).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()