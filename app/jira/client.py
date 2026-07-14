import httpx

from app import config

_client = httpx.Client(
    base_url=config.JIRA_SITE_URL,
    auth=(config.JIRA_EMAIL, config.JIRA_API_TOKEN),
    headers={"Accept": "application/json", "Content-Type": "application/json"},
    timeout=30.0,
)


def _to_adf(text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def create_issue(project_key: str, issue_type: str, summary: str, description: str, fields: dict = None) -> str:
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": _to_adf(description),
            **(fields or {}),
        }
    }
    resp = _client.post("/rest/api/3/issue", json=payload)
    resp.raise_for_status()
    return resp.json()["key"]


def get_issue(issue_key: str) -> dict:
    resp = _client.get(f"/rest/api/3/issue/{issue_key}")
    resp.raise_for_status()
    return resp.json()


def add_comment(issue_key: str, body: str) -> None:
    resp = _client.post(f"/rest/api/3/issue/{issue_key}/comment", json={"body": _to_adf(body)})
    resp.raise_for_status()


def _find_transition(transitions: list, transition_name: str) -> dict | None:
    target = transition_name.lower()

    for t in transitions:
        if t["name"].lower() == target:
            return t
    for t in transitions:
        name = t["name"].lower()
        if target in name or name in target:
            return t
    for t in transitions:
        if t["to"]["name"].lower() == target:
            return t
    for t in transitions:
        if target in t["to"]["name"].lower():
            return t

    return None


def transition_issue(issue_key: str, transition_name: str) -> None:
    resp = _client.get(f"/rest/api/3/issue/{issue_key}/transitions")
    resp.raise_for_status()
    transitions = resp.json()["transitions"]

    match = _find_transition(transitions, transition_name)
    if match is None:
        available = [t["name"] for t in transitions]
        raise ValueError(
            f"No transition named '{transition_name}' available for {issue_key}. Available: {available}"
        )

    resp = _client.post(f"/rest/api/3/issue/{issue_key}/transitions", json={"transition": {"id": match["id"]}})
    resp.raise_for_status()


def search_jql(jql: str, max_results: int = 20) -> list:
    resp = _client.post("/rest/api/3/search/jql", json={"jql": jql, "maxResults": max_results})
    resp.raise_for_status()
    return resp.json()["issues"]
