# AEGIS — Agentic Execution & Governance for Intent-verified Systems

A trust-verified automation layer for Jira: a natural-language interface backed by an LLM intent agent, a risk classifier, a signed-action protocol, human approval for high-risk actions, and an immutable audit trail.

## Setup

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in real values
4. `uvicorn app.main:app --reload`
5. `curl http://localhost:8000/health`
