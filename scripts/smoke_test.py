import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.jira import client as jira_client
from app.llm.nvidia_client import chat


def main():
    print("== Jira: creating test issue ==")
    issue_key = jira_client.create_issue(
        project_key=config.JIRA_PROJECT_KEY,
        issue_type="Task",
        summary="AEGIS smoke test",
        description="Created by scripts/smoke_test.py to verify the Jira client wrapper.",
    )
    print(f"Created issue: {issue_key}")

    print("\n== Jira: fetching it back ==")
    issue = jira_client.get_issue(issue_key)
    print(f"Fetched: {issue['key']} — {issue['fields']['summary']}")

    print("\n== NVIDIA: chat completion ==")
    reply = chat([{"role": "user", "content": "In one sentence, what is a Jira issue?"}])
    print(f"NVIDIA says: {reply}")

    print("\nSmoke test passed.")


if __name__ == "__main__":
    main()
