import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from app import config
from app.jira import client as jira_client

API_BASE_URL = "http://127.0.0.1:8000"
API_KEY = next(iter(config.AEGIS_API_KEYS), "aegis-local-dev-key")


def _print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def _create_demo_ticket(compliance_labeled: bool) -> str:
    key = jira_client.create_issue(
        project_key=config.JIRA_PROJECT_KEY,
        issue_type="Task",
        summary=f"AEGIS demo ticket — {time.strftime('%Y-%m-%d %H:%M:%S')}",
        description="Created by scripts/demo.py for a live AEGIS demo.",
    )
    if compliance_labeled:
        jira_client.set_labels(key, ["compliance"])
    return key


def _submit(text: str) -> dict:
    resp = requests.post(
        f"{API_BASE_URL}/aegis/request",
        json={"text": text},
        headers={"X-AEGIS-API-Key": API_KEY},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _poll_until_resolved(request_id: str, timeout_seconds: int = 180) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        resp = requests.get(f"{API_BASE_URL}/aegis/status/{request_id}", timeout=10)
        body = resp.json()
        if body["status"] != "pending_approval":
            return body
        time.sleep(2)
    return {"status": "timed_out", "request_id": request_id}


def scenario_1_low_risk_auto_execute() -> None:
    _print_header("SCENARIO 1: Low-risk comment -> instant auto-execution")
    key = _create_demo_ticket(compliance_labeled=False)
    print(f"Created demo ticket: {key}")

    text = f"add a comment on {key} saying this is a routine status update"
    print(f'Submitting: "{text}"')
    result = _submit(text)
    print("Result:", result)

    assert result["status"] == "auto_executed", "Expected instant auto-execution"
    print(">>> PASSED: executed instantly, no human involved.")


def scenario_2_high_risk_approve() -> None:
    _print_header("SCENARIO 2: High-risk compliance ticket closure -> Slack approval -> execution")
    key = _create_demo_ticket(compliance_labeled=True)
    print(f"Created compliance-labeled demo ticket: {key}")

    text = f"close {key}"
    print(f'Submitting: "{text}"')
    result = _submit(text)
    print("Result:", result)
    assert result["status"] == "pending_approval", "Expected this to require human approval"

    print(f"\n>>> Go to Slack #aegis now and click APPROVE on the {key} request.")
    print(">>> Waiting for a decision...")
    final = _poll_until_resolved(result["request_id"])
    print("Final status:", final)

    assert final["status"] == "executed", "Expected the approved action to execute"
    print(">>> PASSED: human approved, ticket closed for real.")


def scenario_3_high_risk_deny() -> None:
    _print_header("SCENARIO 3: High-risk request -> Slack denial -> nothing executes")
    key = _create_demo_ticket(compliance_labeled=True)
    print(f"Created compliance-labeled demo ticket: {key}")

    text = f"close {key}"
    print(f'Submitting: "{text}"')
    result = _submit(text)
    print("Result:", result)
    assert result["status"] == "pending_approval", "Expected this to require human approval"

    print(f"\n>>> Go to Slack #aegis now and click DENY on the {key} request.")
    print(">>> Waiting for a decision...")
    final = _poll_until_resolved(result["request_id"])
    print("Final status:", final)

    assert final["status"] == "denied", "Expected the request to be denied"
    print(">>> PASSED: human denied, Jira was never touched.")


SCENARIOS = {
    "1": scenario_1_low_risk_auto_execute,
    "2": scenario_2_high_risk_approve,
    "3": scenario_3_high_risk_deny,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AEGIS demo scenarios against a live server.")
    parser.add_argument("scenario", choices=[*SCENARIOS.keys(), "all"], nargs="?", default="all")
    args = parser.parse_args()

    if args.scenario == "all":
        for run in SCENARIOS.values():
            run()
    else:
        SCENARIOS[args.scenario]()
