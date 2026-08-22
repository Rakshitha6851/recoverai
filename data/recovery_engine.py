import pandas as pd


INPUT_FILE = "data/payments.csv"


def decide_recovery(row):
    """
    Decide the safest recovery action for a failed payment.
    This is a simulation only.
    """

    reason = row["failure_reason"]
    attempts = row["attempt_number"]

    # Safety rule: never retry indefinitely.
    if attempts >= 3:
        return "STOP_AND_ESCALATE"

    # Temporary failures are good candidates for retry.
    if reason in ["timeout", "network_error", "bank_error"]:
        return "RETRY_PAYMENT"

    # Customer-action failures should not be blindly retried.
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

    print("========== RecoverAI Recovery Decisions ==========")

    print(f"Failed payments analyzed: {len(failed):,}")

    print("\nRecommended actions:")

    print(
        failed["recommended_action"]
        .value_counts()
    )

    print("\nSample decisions:")

    print(
        failed[
            [
                "payment_id",
                "amount",
                "failure_reason",
                "attempt_number",
                "recommended_action"
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()