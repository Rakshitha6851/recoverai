import pandas as pd
import random


INPUT_FILE = "data/payments.csv"
OUTPUT_FILE = "data/historical_outcomes.csv"


RECOVERY_PROBABILITY = {
    "timeout": 0.65,
    "network_error": 0.60,
    "bank_error": 0.55,
    "insufficient_funds": 0.35,
    "limit_exceeded": 0.30,
    "authentication_failed": 0.25,
}


def main():

    df = pd.read_csv(INPUT_FILE)

    failed = df[df["status"] == "failed"].copy()

    random.seed(42)

    recovered = []

    for _, row in failed.iterrows():

        probability = RECOVERY_PROBABILITY[
            row["failure_reason"]
        ]

        # Respect the stopping rule.
        if row["attempt_number"] >= 3:
            probability = 0.0

        result = random.random() < probability

        recovered.append(result)

    failed["recovered"] = recovered

    failed["recovered_amount"] = failed.apply(
        lambda row: row["amount"]
        if row["recovered"]
        else 0,
        axis=1
    )

    failed.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("========== Historical Outcomes ==========")
    print(f"Failed payments: {len(failed):,}")
    print(
        f"Recovered payments: "
        f"{failed['recovered'].sum():,}"
    )
    print(
        f"Recovery amount: "
        f"₹{failed['recovered_amount'].sum():,.2f}"
    )
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()