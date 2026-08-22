import pandas as pd


INPUT_FILE = "data/historical_outcomes.csv"


RECOVERY_PROBABILITY = {
    "timeout": 0.65,
    "network_error": 0.60,
    "bank_error": 0.55,
    "insufficient_funds": 0.35,
    "limit_exceeded": 0.30,
    "authentication_failed": 0.25,
}


# Synthetic intervention costs for the experiment.
# These are NOT Razorpay production values.
ACTION_COST = {
    "RETRY_PAYMENT": 20,
    "CUSTOMER_ACTION": 10,
    "AUTHENTICATION": 10,
    "ESCALATE": 5,
}


def choose_action(row):

    reason = row["failure_reason"]
    amount = row["amount"]
    attempts = row["attempt_number"]

    # Hard safety gate.
    if attempts >= 3:
        return "ESCALATE"

    probability = RECOVERY_PROBABILITY[reason]

    expected_recovery = amount * probability

    # Temporary technical failures.
    if reason in [
        "timeout",
        "network_error",
        "bank_error",
    ]:

        if expected_recovery > ACTION_COST["RETRY_PAYMENT"]:
            return "RETRY_PAYMENT"

        return "ESCALATE"

    # Customer-controlled problems.
    if reason in [
        "insufficient_funds",
        "limit_exceeded",
    ]:

        if expected_recovery > ACTION_COST["CUSTOMER_ACTION"]:
            return "CUSTOMER_ACTION"

        return "ESCALATE"

    # Authentication problems.
    if reason == "authentication_failed":

        if expected_recovery > ACTION_COST["AUTHENTICATION"]:
            return "AUTHENTICATION"

        return "ESCALATE"

    return "ESCALATE"


def main():

    df = pd.read_csv(INPUT_FILE)

    df["recommended_action"] = df.apply(
        choose_action,
        axis=1
    )

    print("========== Cost-Aware Recovery Policy ==========")

    print(
        df["recommended_action"]
        .value_counts()
    )

    print("\nAction by failure reason:")

    print(
        pd.crosstab(
            df["failure_reason"],
            df["recommended_action"]
        )
    )


if __name__ == "__main__":
    main()