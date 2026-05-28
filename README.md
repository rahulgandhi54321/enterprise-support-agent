# Enterprise AI Customer Support Operator

This is a live agent prototype for classifying and handling customer support requests across email, chat, CRM, WhatsApp, Slack, and support portals.

The browser console includes operational panels for intake, CRM context, order context, matched policies, risk flags, tool actions, audit status, and response drafting.
It also exposes recent audit events and operations summary data from the backend.

The agent returns:

- Ticket category
- Priority
- Sentiment
- Suggested action
- Draft reply
- Escalation status
- Confidence score
- Tool actions performed

## Run Locally

Use Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py --sample angry_refund
```

Start the HTTP API:

```bash
source .venv/bin/activate
python main.py
```

Open the browser console:

```text
http://127.0.0.1:8000
```

Then call:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/ops/summary
curl -s http://127.0.0.1:8000/audit/recent
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H 'content-type: application/json' \
  -d '{"channel":"email","customer_id":"cus_vip_001","message":"I was charged twice and nobody has responded. Refund me today or I will cancel."}'
```

## Safety Model

- Refunds above the configured threshold are routed to human approval.
- Legal complaints, security incidents, high churn risk, high anger, and low confidence are escalated.
- The prototype uses mock tools and fixture data only. It never fabricates an actual refund, account change, or fulfillment action.
- Every tool call is logged to `audit_logs/actions.jsonl`.

## Environment

Copy `.env.example` to `.env.local` and set `OPENAI_API_KEY`. The Codex setup for this project already created `.env.local`.
