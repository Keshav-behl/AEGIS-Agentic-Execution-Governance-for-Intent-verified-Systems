# AEGIS — Agentic Execution & Governance for Intent-verified Systems

A trust-verified automation layer for Jira: a natural-language interface backed by an LLM intent agent, a risk classifier, a signed-action protocol, human approval for high-risk actions, and an immutable audit trail.

## Setup

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in real values
4. `uvicorn app.main:app --reload`
5. `curl http://localhost:8000/health`

## Using AEGIS

With the API running, submit a natural-language request:

```
curl -X POST http://localhost:8000/aegis/request \
  -H "Content-Type: application/json" \
  -d '{"text": "add a comment on AG-1 saying deployment is complete"}'
```

Low-risk requests execute immediately against Jira. High-risk requests are posted to Slack
for human approval and return `pending_approval` — poll `GET /aegis/status/{request_id}` to
see when a decision has been made.

### Chat UI (Streamlit)

```
streamlit run streamlit_app.py
```

A minimal chat front-end that posts to `/aegis/request` and shows the outcome — the free
alternative to wiring this up as a ChatGPT Custom GPT via `openapi/aegis_actions.yaml`.
