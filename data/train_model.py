import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix


INPUT_FILE = "data/historical_outcomes.csv"


def main():

    df = pd.read_csv(INPUT_FILE)

    # Features used by the model.
    X = df[
        [
            "amount",
            "payment_method",
            "failure_reason",
            "attempt_number",
        ]
    ]

    # Target: whether the payment was eventually recovered.
    y = df["recovered"]

    # 80% training, 20% held-out testing.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    categorical_features = [
        "payment_method",
        "failure_reason",
    ]

    numerical_features = [
        "amount",
        "attempt_number",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "numerical",
                "passthrough",
                numerical_features,
            ),
        ]
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    print("========== RecoverAI ML Evaluation ==========")

    print(f"Training records: {len(X_train):,}")
    print(f"Test records: {len(X_test):,}")

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            predictions,
            target_names=["Not recovered", "Recovered"],
        )
    )

    print("Confusion matrix:")

    print(confusion_matrix(y_test, predictions))


if __name__ == "__main__":
    main()