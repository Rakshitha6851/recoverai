import pandas as pd
import random


INPUT_FILE = "data/payments.csv"


RECOVERY_PROBABILITY = {
    "RETRY_PAYMENT": 0.60,
    "CUSTOMER_ACTION_REQUIRED": 0.35,
    "CUSTOMER_AUTHENTICATION_REQUIRED": 0.30,
    "STOP_AND_ESCALATE": 0.00,
}


def recoverai_decision(row):
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


def simulate(probability, seed):
    random.seed(seed)

    return random.random() < probability


def main():

    df = pd.read_csv(INPUT_FILE)

    failed = df[df["status"] == "failed"].copy()

    # -------------------------------------------------
    # STRATEGY A: NAIVE RETRY
    # -------------------------------------------------

    naive = failed[
        failed["attempt_number"] < 3
    ].copy()

    naive["recovered"] = naive.apply(
        lambda row: simulate(0.40, 42 + row.name),
        axis=1
    )

    naive["recovered_amount"] = naive.apply(
        lambda row: row["amount"]
        if row["recovered"]
        else 0,
        axis=1
    )

    naive_recovered = naive["recovered_amount"].sum()
    naive_attempted = len(naive)
    naive_recovered_count = naive["recovered"].sum()

    # -------------------------------------------------
    # STRATEGY B: RECOVERAI
    # -------------------------------------------------

    ai = failed.copy()

    ai["recommended_action"] = ai.apply(
        recoverai_decision,
        axis=1
    )

    ai["recovered"] = False

    for index, row in ai.iterrows():

        action = row["recommended_action"]

        probability = RECOVERY_PROBABILITY.get(
            action,
            0.0
        )

        if simulate(probability, 1000 + index):
            ai.loc[index, "recovered"] = True

    ai["recovered_amount"] = ai.apply(
        lambda row: row["amount"]
        if row["recovered"]
        else 0,
        axis=1
    )

    ai_recovered = ai["recovered_amount"].sum()
    ai_attempted = (
        ai["recommended_action"] == "RETRY_PAYMENT"
    ).sum()

    ai_recovered_count = ai["recovered"].sum()

    total_at_risk = failed["amount"].sum()

    # -------------------------------------------------
    # RESULTS
    # -------------------------------------------------

    print("========== RecoverAI Strategy Comparison ==========")

    print(f"\nTotal failed payments: {len(failed):,}")

    print(f"Total revenue at risk: ₹{total_at_risk:,.2f}")

    print("\n--------------- NAIVE RETRY ----------------")

    print(
        f"Payments attempted: {naive_attempted:,}"
    )

    print(
        f"Payments recovered: {naive_recovered_count:,}"
    )

    print(
        f"Revenue recovered: ₹{naive_recovered:,.2f}"
    )

    print(
        f"Recovery rate: "
        f"{naive_recovered / total_at_risk * 100:.2f}%"
    )

    print("\n--------------- RECOVERAI ----------------")

    print(
        f"Payments attempted: {ai_attempted:,}"
    )

    print(
        f"Payments recovered: {ai_recovered_count:,}"
    )

    print(
        f"Revenue recovered: ₹{ai_recovered:,.2f}"
    )

    print(
        f"Recovery rate: "
        f"{ai_recovered / total_at_risk * 100:.2f}%"
    )

    print("\n--------------- IMPACT ----------------")

    print(
        f"Additional revenue recovered: "
        f"₹{ai_recovered - naive_recovered:,.2f}"
    )

    print(
        f"Reduction in payment retries: "
        f"{naive_attempted - ai_attempted:,}"
    )

    print("\nStopping rule:")

    print(
        "RecoverAI does not retry payments with "
        "3 or more previous attempts."
    )


if __name__ == "__main__":
    main()