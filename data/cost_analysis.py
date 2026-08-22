import pandas as pd


INPUT_FILE = "data/historical_outcomes.csv"


def main():

    df = pd.read_csv(INPUT_FILE)

    # Our current rule:
    # temporary payment failures are considered recoverable.
    df["predicted_recoverable"] = df[
        "failure_reason"
    ].isin(
        [
            "timeout",
            "network_error",
            "bank_error",
        ]
    )

    actual = df["recovered"]
    predicted = df["predicted_recoverable"]

    true_positive = ((predicted == True) & (actual == True)).sum()
    false_positive = ((predicted == True) & (actual == False)).sum()
    false_negative = ((predicted == False) & (actual == True)).sum()
    true_negative = ((predicted == False) & (actual == False)).sum()

    missed_revenue = df[
        (predicted == False) &
        (actual == True)
    ]["amount"].sum()

    unnecessary_action_amount = df[
        (predicted == True) &
        (actual == False)
    ]["amount"].sum()

    print("========== RecoverAI Cost Analysis ==========")

    print(f"True positives: {true_positive:,}")
    print(f"False positives: {false_positive:,}")
    print(f"False negatives: {false_negative:,}")
    print(f"True negatives: {true_negative:,}")

    print(
        f"\nMissed recoverable revenue: "
        f"₹{missed_revenue:,.2f}"
    )

    print(
        f"Revenue exposed to unsuccessful recovery: "
        f"₹{unnecessary_action_amount:,.2f}"
    )


if __name__ == "__main__":
    main()