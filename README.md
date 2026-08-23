<p align="center">
  <img src="https://img.shields.io/badge/RecoverAI-Failed%20Payment%20Recovery-8A2BE2?style=for-the-badge" alt="RecoverAI" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Python-ML%20%2B%20Rules-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</p>

<hr />

**NOTE:** The dashboard runs locally after starting the FastAPI server; 127.0.0.1 refers to the machine running the application.

# RecoverAI TEST

## AI Failed Payment Recovery Agent

RecoverAI is an AI-assisted failed-payment recovery system designed to identify failed payments, diagnose failure reasons, choose a safe recovery intervention, execute bounded recovery, and record an auditable outcome.

# Note: The dashboard runs locally after starting the FastAPI server. 127.0.0.1 refers to the machine running the application.

## Problem

Failed payments create direct revenue risk for payment platforms and merchants.

A naive approach is to retry failed payments broadly. This can cause:

unnecessary retries

repeated failures

poor customer experience

avoidable operational cost

retries that should have been stopped

RecoverAI uses failure-aware recovery decisions and explicit stopping rules instead of blindly retrying every failed payment.

## Solution

**RecoverAI follows a four-stage recovery workflow:**

1. Detect

Identify failed payments and calculate revenue at risk.

2. Diagnose

Determine why the payment failed.

Examples:

network_error

timeout

bank_error

insufficient_funds

limit_exceeded

authentication_failed

3. Decide

Select the safest recovery intervention.

RecoverAI can recommend:

RETRY_PAYMENT

CUSTOMER_ACTION

AUTHENTICATION

ESCALATE

4. Recover

Execute a bounded recovery workflow using:

historical outcomes

recovery decisions

stopping rules

audit records

Architecture

Failed Payments
      |
      v
Detect & Diagnose
      |
      v
RecoverAI Decision Engine
      |
      +-------------------+
      |         |         |
      v         v         v
    Retry   Customer   Escalate
            Action
      |
      v
Bounded Recovery
      |
      v
Historical Outcome
      |
      v
Audit Trail + Batch Impact

Dataset

The project uses synthetic payment data.

Current dataset:

Total payments: 5,000

Failed payments: 1,327

Revenue at risk: ₹3,504,173

Historical outcomes contain recovery results for the failed-payment dataset.

Recovery Decision Policy

RecoverAI uses failure-aware decision rules.

Failure reason

Recovery action

timeout

Retry

network_error

Retry

bank_error

Retry

insufficient_funds

Customer action

limit_exceeded

Customer action

authentication_failed

Authentication

3+ previous attempts

Escalate

Safety Controls

RecoverAI does not blindly retry payments.

Maximum retry rule

Payments with 3 or more previous attempts are stopped and escalated.

Attempt 1 -> Recovery may be attempted
Attempt 2 -> Recovery may be attempted
Attempt 3 -> STOP
             |
             v
          ESCALATE

Customer-controlled failures are not automatically retried.

Recovery Outcomes

The system records different recovery outcomes.

Successful

RECOVERY_RECORDED

Failed

RECOVERY_FAILED

Stopped / Escalated

ESCALATION_REQUIRED

Batch Impact

RecoverAI was compared with a naive retry strategy across 1,327 failed payments.

Both /metrics and /strategy-comparison compute the comparison from the same source data:

data/payments.csv

data/historical_outcomes.csv

Therefore, these are the figures returned by the current running application.

Metric

Result

Naive retry revenue recovered

₹10,44,996

RecoverAI revenue recovered

₹13,98,558

Additional revenue recovered

₹3,53,562

Retries reduced

661

RecoverAI recovered an additional ₹3,53,562 while reducing payment retries by 661 in the current batch comparison.

## Comparison methodology

For technical failures (timeout, network_error, bank_error), a blind retry is treated as an appropriate intervention, so the naive strategy and RecoverAI receive the same recovery credit.

For customer-controlled failures (insufficient_funds, limit_exceeded, authentication_failed), a blind retry is assumed to recover only a fraction of cases because it does not address the underlying problem.

The current implementation uses fixed effectiveness assumptions for the naive counterfactual:

35% for funds/limit issues

20% for authentication issues

These are disclosed modelling assumptions in backend/main.py (NAIVE_RETRY_EFFECTIVENESS). They are not fitted or tuned ML parameters. RecoverAI's own recovered amount comes from the recorded historical outcomes.

## Evaluation & Safety

The project includes both ML experimentation and a rule-based/cost-aware decision layer.

Metric

Result

Rule baseline accuracy

63%

ML model accuracy

53%

Missed recoverable revenue

₹5,12,600

Unsuccessful recovery exposure

₹7,74,314

The production recovery workflow is constrained by explicit policy and safety rules rather than relying on an unconstrained ML prediction.

**Why rules, not ML?**

An ML classifier was trained on historical outcomes to predict recovery success. It underperformed the rule baseline on the current evaluation (53% vs 63% accuracy).

For a workflow that decides whether to retry a customer's payment or escalate a payment, explainability and bounded execution matter. A wrong prediction can cause a wasted retry or a missed recovery, while an opaque model makes it harder to explain why a particular action was selected.

Therefore, RecoverAI uses the rule-based / cost-aware policy in backend/main.py as the decision engine. The ML experiment in data/train_model.py remains as a documented comparison rather than being silently discarded.

If a future model clearly outperforms the rule baseline on held-out data and can provide per-decision explanations, it could be considered as an augmentation or replacement for the current policy.

Auditability

**Every recovery decision can be associated with an audit record containing:**

payment ID

amount

failure reason

attempt number

recommended action

decision reason

expected recovery value

audit status

This allows recovery decisions to be inspected after execution.

Dashboard

The RecoverAI dashboard provides:

failed payment metrics

revenue at risk

revenue recovered

recovery rate

payment-level recovery decisions

expected recovery value

stopping rules

audit status

batch recovery impact

evaluation and safety metrics

Examples

Retry example

For a payment such as:

Payment ID: pay_00006
Amount: ₹1,999
Failure: network_error
Attempt: 1

RecoverAI recommends:

RETRY_PAYMENT

The bounded recovery workflow can then record whether the recovery actually succeeded.

Escalation example

For a payment such as:

Payment ID: pay_00035
Attempt: 3

RecoverAI applies the stopping rule:

ESCALATION_REQUIRED

No additional automatic retry is performed.

Simulation Disclosure

POST /payments/{payment_id}/recover does not call a live payment gateway.

It executes the safety gate and policy checks for the payment, then looks up the pre-computed outcome for that payment in data/historical_outcomes.csv.

This makes the full:

Detect → Diagnose → Decide → Recover → Audit

loop demonstrable end-to-end without requiring a live payment gateway.

A future live integration would replace the historical-outcome lookup with an actual retry or customer-notification API call. The decision logic, stopping rules, and audit trail can remain around that integration.

Failure Recovery — What Broke and What We Did

Being transparent about problems found while building RecoverAI:

The ML model underperformed the rule baseline. The model achieved 53% accuracy versus 63% for the rule baseline. Instead of forcing the weaker model into the recovery path, we kept the comparison documented and shipped the rule-based policy as the decision engine.

The batch comparison and dashboard metrics originally used different calculation paths. This produced inconsistent numbers. We consolidated the comparison into shared backend logic so /metrics and /strategy-comparison use the same source data and calculation.

The naive-vs-RecoverAI comparison initially did not demonstrate additional revenue clearly. We changed the naive strategy counterfactual to account for the failure reason and disclosed the modelling assumptions instead of hiding them.

The backend had duplicated route definitions during iterative development. These were cleaned up into a single set of routes with shared helper functions.

The dashboard initially had a frontend element-ID mismatch. This caused a JavaScript null element error when updating the audit status. The HTML IDs and JavaScript references were aligned and the dashboard flow was tested again.

Technology

Python

FastAPI

Pandas

Scikit-learn

HTML

CSS

JavaScript

Uvicorn

## Running the Project

1. Create a virtual environment

python -m venv .venv

2. Activate it

.venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Start the FastAPI backend

## uvicorn backend.main:app --reload

The dashboard runs locally after the backend starts.

## Open the dashboard:

http://127.0.0.1:8000/dashboard

## API documentation:

http://127.0.0.1:8000/docs

Key API Endpoints

GET  /
GET  /metrics
GET  /strategy-comparison
GET  /dashboard
GET  /payments/{payment_id}
POST /payments/{payment_id}/recover

Project Structure

recoverai/
|
├── backend/
│   ├── _init_.py
│   └── main.py
|
├── frontend/
│   └── index.html
|
├── data/
│   ├── payments.csv
│   ├── historical_outcomes.csv
│   ├── audit_trail.csv
│   ├── generate_data.py
│   ├── analyze_data.py
│   ├── recovery_engine.py
│   ├── recovery_simulator.py
│   ├── compare_strategies.py
│   ├── historical_outcomes.py
│   ├── train_model.py
│   ├── rule_baseline.py
│   ├── cost_analysis.py
│   ├── cost_aware_policy.py
│   └── generate_audit.py
|
├── requirements.txt
├── .gitignore
└── README.md

Buildathon Focus

RecoverAI focuses on intelligent failed-payment recovery through:

Detect → Diagnose → Decide → Recover → Audit

The key design principle is:

Recover revenue without blindly retrying payments.

# THANK YOU