**NOTE:** The dashboard runs locally after starting the FastAPI server; 127.0.0.1 refers to the machine running the application.

# RecoverAI

## AI Failed Payment Recovery Agent

RecoverAI is an AI-assisted failed-payment recovery system designed to identify failed payments, diagnose failure reasons, choose a safe recovery intervention, execute bounded recovery, and record an auditable outcome.

> **Note:** The dashboard runs locally after starting the FastAPI server. `127.0.0.1` refers to the machine running the application.

## Problem

Failed payments create direct revenue risk for payment platforms and merchants.

A naive approach is to retry failed payments broadly. This can cause:

- unnecessary retries
- repeated failures
- poor customer experience
- avoidable operational cost
- retries that should have been stopped

RecoverAI uses failure-aware recovery decisions and explicit stopping rules instead of blindly retrying every failed payment.

## Solution

RecoverAI follows a four-stage recovery workflow:

### 1. Detect

Identify failed payments and calculate revenue at risk.

### 2. Diagnose

Determine why the payment failed.

Examples:

- `network_error`
- `timeout`
- `bank_error`
- `insufficient_funds`
- `limit_exceeded`
- `authentication_failed`

### 3. Decide

Select the safest recovery intervention.

RecoverAI can recommend:

- `RETRY_PAYMENT`
- `CUSTOMER_ACTION`
- `AUTHENTICATION`
- `ESCALATE`

### 4. Recover

Execute a bounded recovery workflow using:

- historical outcomes
- recovery decisions
- stopping rules
- audit records

## Architecture

```text
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

Failure reason	Recovery action
timeout	Retry
network_error	Retry
bank_error	Retry
insufficient_funds	Customer action
limit_exceeded	Customer action
authentication_failed	Authentication
3+ previous attempts	Escalate
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

Metric	Result
Naive retry revenue recovered	₹12,65,701
RecoverAI revenue recovered	₹15,67,429
Additional revenue recovered	₹3,01,728
Retries reduced	661

RecoverAI recovered an additional ₹3,01,728 while reducing payment retries by 661 in the simulated batch comparison.

Note: The batch comparison figures above come from the simulated strategy comparison. The dashboard's historical outcome metrics are reported separately.

Evaluation & Safety

The project includes both ML experimentation and a rule-based/cost-aware decision layer.

Metric	Result
Rule baseline accuracy	63%
ML model accuracy	53%
Missed recoverable revenue	₹5,12,600
Unsuccessful recovery exposure	₹7,74,314

The production recovery workflow is constrained by explicit policy and safety rules rather than relying on an unconstrained ML prediction.

Auditability

Every recovery decision can be associated with an audit record containing:

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
Example

For a payment such as:

Payment ID: pay_00006
Amount: ₹1,999
Failure: network_error
Attempt: 1

RecoverAI recommends:

RETRY_PAYMENT

The bounded recovery workflow can then record whether the recovery actually succeeded.

For a payment such as:

Payment ID: pay_00035
Attempt: 3

RecoverAI applies the stopping rule:

ESCALATION_REQUIRED

No additional automatic retry is performed.

Technology
Python
FastAPI
Pandas
Scikit-learn
HTML
CSS
JavaScript
Uvicorn
Running the Project

Activate the virtual environment:

.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Start the FastAPI backend:

uvicorn backend.main:app --reload

The dashboard runs locally after the backend starts.

Open the dashboard:

http://127.0.0.1:8000/dashboard

API documentation:

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
├── frontend/
│   └── index.html
|
├── requirements.txt
├── .gitignore
└── README.md
Buildathon Focus

RecoverAI focuses on intelligent failed-payment recovery through:

Detect → Diagnose → Decide → Recover → Audit

The key design principle is:

Recover revenue without blindly retrying payments.