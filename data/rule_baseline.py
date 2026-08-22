import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix


INPUT_FILE = "data/historical_outcomes.csv"


def rule_prediction(reason):
    if reason in ["timeout", "network_error", "bank_error"]:
        return True

    return False


def main():

    df = pd.read_csv(INPUT_FILE)

    predictions = df["failure_reason"].apply(
        rule_prediction
    )

    print("========== RecoverAI Rule Baseline ==========")

    print(
        classification_report(
            df["recovered"],
            predictions,
            target_names=[
                "Not recovered",
                "Recovered"
            ]
        )
    )

    print("Confusion matrix:")

    print(
        confusion_matrix(
            df["recovered"],
            predictions
        )
    )


if __name__ == "__main__":
    main()