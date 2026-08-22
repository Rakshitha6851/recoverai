import pandas as pd
from pathlib import Path


data_path = Path(__file__).parent / "payments.csv"

df = pd.read_csv(data_path)

failed_payments = df[df["status"] == "failed"]

revenue_at_risk = failed_payments["amount"].sum()

print("========== RecoverAI Data Analysis ==========")
print(f"Total payments: {len(df):,}")
print(f"Failed payments: {len(failed_payments):,}")
print(f"Revenue at risk: ₹{revenue_at_risk:,.2f}")

print()
print("Failure reasons:")
print(failed_payments["failure_reason"].value_counts())

print()
print("Average failed payment:")
print(f"₹{failed_payments['amount'].mean():,.2f}")