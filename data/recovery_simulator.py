import pandas as pd
import random


INPUT_FILE = "data/payments.csv"


# Synthetic recovery probabilities for the experiment.
# These are NOT real Razorpay probabilities.
RECOVERY_PROBABILITY = {
    "RETRY_PAYMENT": 0.60,
    "CUSTOMER_ACTION_REQUIRED": 0.35,
    "CUSTOMER_AUTHENTICATION_REQUIRED": 0.30,
    "STOP_AND_ESCALATE": 0.00,
}


def decide_recovery(row):
    reason = row["failure_reason"]
    attempts = row["attempt_number"]

    if attempts >= 3:
        return "STOP_AND_ESCALATE"

    if reason in ["timeout", "network_error", "bank_error"]:
        return "RETRY_PAYMENT"

    if reason in ["insufficient_funds", "limit_exceeded"]:
        return "CUSTOMER_ACTION_REQUIRED"

    if reason == "authentication_failed":
        return "CUSTOMER_AUTHENTICATION_REQUIRED"

    return "MANUAL_REVIEW"


def main():

    df = pd.read_csv(INPUT_FILE)

    failed = df[df["status"] == "failed"].copy()

    failed["recommended_action"] = failed.apply(
        decide_recovery,
        axis=1
    )

    random.seed(42)

    failed["recovered"] = False

    for index, row in failed.iterrows():

        action = row["recommended_action"]

        probability = RECOVERY_PROBABILITY.get(
            action,
            0.0
        )

        if random.random() < probability:
            failed.loc[index, "recovered"] = True

    failed["recovered_amount"] = failed.apply(
        lambda row: row["amount"]
        if row["recovered"]
        else 0,
        axis=1
    )

    total_at_risk = failed["amount"].sum()

    total_recovered = failed["recovered_amount"].sum()

    recovered_count = failed["recovered"].sum()

    recovery_rate = (
        total_recovered / total_at_risk * 100
        if total_at_risk > 0
        else 0
    )

    print("========== RecoverAI Recovery Simulation ==========")

    print(f"Failed payments: {len(failed):,}")

    print(f"Revenue at risk: ₹{total_at_risk:,.2f}")

    print(f"Payments recovered: {recovered_count:,}")

    print(f"Revenue recovered: ₹{total_recovered:,.2f}")

    print(f"Recovery rate: {recovery_rate:.2f}%")

    print("\nRecovery by action:")

    summary = (
        failed
        .groupby("recommended_action")
        .agg(
            payments=("payment_id", "count"),
            recovered_payments=("recovered", "sum"),
            amount_at_risk=("amount", "sum"),
            amount_recovered=("recovered_amount", "sum"),
        )
    )

    print(summary.to_string())

    print("\nSample recovery results:")

    print(
        failed[
            [
                "payment_id",
                "amount",
                "failure_reason",
                "recommended_action",
                "recovered",
                "recovered_amount",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()