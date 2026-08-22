import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


OUTPUT_FILE = Path("data/payments.csv")
NUMBER_OF_PAYMENTS = 5000


PAYMENT_METHODS = [
    "upi",
    "card",
    "netbanking",
    "wallet",
]


FAILURE_REASONS = [
    "timeout",
    "insufficient_funds",
    "bank_error",
    "network_error",
    "authentication_failed",
    "limit_exceeded",
]


def generate_payment(payment_number):
    amount = random.choice([
        199, 299, 499, 999, 1499,
        1999, 2499, 4999, 9999
    ])

    payment_method = random.choice(PAYMENT_METHODS)

    # Most payments succeed; some fail.
    status = random.choices(
        ["success", "failed"],
        weights=[75, 25],
        k=1
    )[0]

    if status == "failed":
        failure_reason = random.choice(FAILURE_REASONS)
    else:
        failure_reason = ""

    attempt_number = random.choices(
        [1, 2, 3],
        weights=[75, 20, 5],
        k=1
    )[0]

    created_at = datetime.now() - timedelta(
        days=random.randint(0, 30),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )

    return {
        "payment_id": f"pay_{payment_number:05d}",
        "customer_id": f"cust_{random.randint(1, 1500):04d}",
        "amount": amount,
        "payment_method": payment_method,
        "status": status,
        "failure_reason": failure_reason,
        "attempt_number": attempt_number,
        "created_at": created_at.isoformat(),
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    payments = [
        generate_payment(i)
        for i in range(1, NUMBER_OF_PAYMENTS + 1)
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=payments[0].keys()
        )

        writer.writeheader()
        writer.writerows(payments)

    print(f"Generated {NUMBER_OF_PAYMENTS} payments.")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()